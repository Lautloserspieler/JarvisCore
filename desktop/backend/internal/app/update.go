package app

import (
	"encoding/json"
	"fmt"
	"net/http"
	"runtime"
	"strings"
	"time"

	"github.com/Masterminds/semver/v3"
)

// UpdateInfo contains information about available updates
type UpdateInfo struct {
	Available      bool   `json:"available"`
	CurrentVersion string `json:"current_version"`
	LatestVersion  string `json:"latest_version"`
	ReleaseURL     string `json:"release_url"`
	Changelog      string `json:"changelog"`
	DownloadURL    string `json:"download_url"`
	PublishedAt    string `json:"published_at"`
}

// UpdateSettings contains user preferences for auto-update
type UpdateSettings struct {
	AutoCheck      bool   `json:"auto_check"`
	AutoDownload   bool   `json:"auto_download"`
	CheckInterval  string `json:"check_interval"` // "daily", "weekly", "startup", "never"
	NotifyUpdates  bool   `json:"notify_updates"`
	LastCheckTime  string `json:"last_check_time"`
}

var (
	// Version is injected at build time via ldflags
	// Example: wails build -ldflags "-X 'github.com/Lautloserspieler/JarvisCore/desktop/backend/internal/app.Version=v1.0.1'"
	Version = "v1.0.0" // Default fallback
)

const (
	GitHubRepo = "Lautloserspieler/JarvisCore"
	GitHubAPI  = "https://api.github.com/repos/" + GitHubRepo + "/releases/latest"
)

// CheckForUpdates queries GitHub API for latest release
func (a *App) CheckForUpdates() (UpdateInfo, error) {
	// Create HTTP client with timeout
	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	// Fetch latest release from GitHub
	resp, err := client.Get(GitHubAPI)
	if err != nil {
		return UpdateInfo{}, fmt.Errorf("failed to fetch releases: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return UpdateInfo{}, fmt.Errorf("GitHub API returned status %d", resp.StatusCode)
	}

	// Parse GitHub release response
	var release struct {
		TagName     string    `json:"tag_name"`
		Body        string    `json:"body"`
		HtmlURL     string    `json:"html_url"`
		PublishedAt time.Time `json:"published_at"`
		Assets      []struct {
			Name               string `json:"name"`
			BrowserDownloadURL string `json:"browser_download_url"`
		} `json:"assets"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&release); err != nil {
		return UpdateInfo{}, fmt.Errorf("failed to parse release data: %w", err)
	}

	// Compare versions using semver
	currentVer, err := semver.NewVersion(strings.TrimPrefix(Version, "v"))
	if err != nil {
		return UpdateInfo{}, fmt.Errorf("invalid current version: %w", err)
	}

	latestVer, err := semver.NewVersion(strings.TrimPrefix(release.TagName, "v"))
	if err != nil {
		return UpdateInfo{}, fmt.Errorf("invalid latest version: %w", err)
	}

	updateAvailable := latestVer.GreaterThan(currentVer)

	// Find download URL for current OS
	downloadURL := ""
	for _, asset := range release.Assets {
		// Match OS-specific binaries
		name := strings.ToLower(asset.Name)
		if strings.Contains(name, runtime.GOOS) {
			// Prefer exact architecture match
			if strings.Contains(name, runtime.GOARCH) || runtime.GOARCH == "amd64" {
				downloadURL = asset.BrowserDownloadURL
				break
			}
			if downloadURL == "" {
				downloadURL = asset.BrowserDownloadURL
			}
		}
	}

	return UpdateInfo{
		Available:      updateAvailable,
		CurrentVersion: Version,
		LatestVersion:  release.TagName,
		ReleaseURL:     release.HtmlURL,
		Changelog:      release.Body,
		DownloadURL:    downloadURL,
		PublishedAt:    release.PublishedAt.Format("2006-01-02 15:04:05"),
	}, nil
}

// GetUpdateSettings retrieves current update settings
func (a *App) GetUpdateSettings() (UpdateSettings, error) {
	// TODO: Load from config file or database
	// For now, return defaults
	return UpdateSettings{
		AutoCheck:      true,
		AutoDownload:   false,
		CheckInterval:  "daily",
		NotifyUpdates:  true,
		LastCheckTime:  time.Now().Format(time.RFC3339),
	}, nil
}

// SaveUpdateSettings persists update settings
func (a *App) SaveUpdateSettings(settings UpdateSettings) error {
	// TODO: Save to config file or database
	// For now, just validate
	validIntervals := map[string]bool{
		"daily":   true,
		"weekly":  true,
		"startup": true,
		"never":   true,
	}

	if !validIntervals[settings.CheckInterval] {
		return fmt.Errorf("invalid check interval: %s", settings.CheckInterval)
	}

	// Update last check time
	settings.LastCheckTime = time.Now().Format(time.RFC3339)

	return nil
}

// GetCurrentVersion returns the current application version
func (a *App) GetCurrentVersion() string {
	return Version
}
