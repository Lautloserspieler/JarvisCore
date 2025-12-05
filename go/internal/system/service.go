package system

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/shirou/gopsutil/v4/disk"
	"github.com/shirou/gopsutil/v4/host"
	"github.com/shirou/gopsutil/v4/mem"
	"github.com/shirou/gopsutil/v4/net"
)

// Config haelt Laufzeitparameter.
type Config struct {
	ListenAddr string
}

// LoadConfig liest Umgebungsvariablen ein.
func LoadConfig() Config {
	addr := os.Getenv("SYSTEMD_LISTEN")
	if addr == "" {
		addr = ":7073"
	}
	return Config{ListenAddr: addr}
}

// Service kapselt Handler und Logger.
type Service struct {
	cfg    Config
	logger *log.Logger
}

// NewService erstellt einen neuen Service.
func NewService(cfg Config, logger *log.Logger) *Service {
	if logger == nil {
		logger = log.New(os.Stdout, "[systemd] ", log.LstdFlags|log.LUTC)
	}
	return &Service{cfg: cfg, logger: logger}
}

// Routes registriert HTTP-Endpunkte.
func (s *Service) Routes(mux *http.ServeMux) {
	mux.HandleFunc("/system/resources", s.handleResources)
	mux.HandleFunc("/system/status", s.handleStatus)
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "timestamp": time.Now().UTC()})
	})
}

func (s *Service) handleResources(w http.ResponseWriter, r *http.Request) {
	res, err := s.collectResources()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "collect_failed", err)
		return
	}
	writeJSON(w, http.StatusOK, res)
}

func (s *Service) handleStatus(w http.ResponseWriter, r *http.Request) {
	status, err := s.collectStatus()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "collect_failed", err)
		return
	}
	writeJSON(w, http.StatusOK, status)
}

// collectResources liefert CPU/Mem/Disk/Net-Basics.
func (s *Service) collectResources() (map[string]any, error) {
	cpuPercent, err := cpu.Percent(200*time.Millisecond, true)
	if err != nil {
		return nil, err
	}
	vm, err := mem.VirtualMemory()
	if err != nil {
		return nil, err
	}
	swap, _ := mem.SwapMemory()
	partitions, _ := disk.Partitions(false)
	disks := make([]map[string]any, 0, len(partitions))
	for _, p := range partitions {
		if u, err := disk.Usage(p.Mountpoint); err == nil {
			disks = append(disks, map[string]any{
				"path":    u.Path,
				"fstype":  p.Fstype,
				"total":   u.Total,
				"used":    u.Used,
				"free":    u.Free,
				"percent": u.UsedPercent,
			})
		}
	}
	netIO, _ := net.IOCounters(true)
	ifaces, _ := net.Interfaces()
	ifaceInfo := make([]map[string]any, 0, len(ifaces))
	for _, n := range ifaces {
		ifaceInfo = append(ifaceInfo, map[string]any{
			"name":  n.Name,
			"flags": n.Flags,
			"addrs": n.Addrs,
		})
	}
	payload := map[string]any{
		"cpu_percent": cpuPercent,
		"memory": map[string]any{
			"total":   vm.Total,
			"used":    vm.Used,
			"free":    vm.Free,
			"percent": vm.UsedPercent,
		},
		"swap": map[string]any{
			"total":   swap.Total,
			"used":    swap.Used,
			"free":    swap.Free,
			"percent": swap.UsedPercent,
		},
		"disks": disks,
	}
	if len(netIO) > 0 {
		netStats := make([]map[string]any, 0, len(netIO))
		for _, n := range netIO {
			netStats = append(netStats, map[string]any{
				"name":        n.Name,
				"bytes_sent":  n.BytesSent,
				"bytes_recv":  n.BytesRecv,
				"packets_in":  n.PacketsRecv,
				"packets_out": n.PacketsSent,
				"err_in":      n.Errin,
				"err_out":     n.Errout,
				"drop_in":     n.Dropin,
				"drop_out":    n.Dropout,
			})
		}
		payload["network"] = netStats
	}
	payload["interfaces"] = ifaceInfo
	return payload, nil
}

// collectStatus liefert Host-Infos.
func (s *Service) collectStatus() (map[string]any, error) {
	info, err := host.Info()
	if err != nil {
		return nil, err
	}
	return map[string]any{
		"hostname":       info.Hostname,
		"uptime":         info.Uptime,
		"boot_time":      info.BootTime,
		"os":             info.OS,
		"platform":       info.Platform,
		"platform_ver":   info.PlatformVersion,
		"kernel":         info.KernelVersion,
		"kernel_arch":    info.KernelArch,
		"virtualization": info.VirtualizationSystem,
	}, nil
}

func firstOrZero(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	return values[0]
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, status int, code string, err error) {
	if err == nil {
		err = errors.New(code)
	}
	writeJSON(w, status, map[string]any{
		"error":   code,
		"message": err.Error(),
	})
}
