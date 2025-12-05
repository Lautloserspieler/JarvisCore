package main

import (
	"embed"
	"log"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	"github.com/wailsapp/wails/v2/pkg/options/windows"

	"jarviscore/desktop/internal/app"
)

//go:embed all:../frontend/dist
var assets embed.FS

func main() {
	// JarvisCore App initialisieren
	jarvisApp := app.NewApp()

	// Wails-Konfiguration
	err := wails.Run(&options.App{
		Title:      "J.A.R.V.I.S. Desktop",
		Width:      1280,
		Height:     800,
		MinWidth:   1024,
		MinHeight:  600,
		
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		
		BackgroundColour: &options.RGBA{R: 30, G: 30, B: 30, A: 1},
		
		OnStartup:  jarvisApp.Startup,
		OnShutdown: jarvisApp.Shutdown,
		
		// Go-Funktionen für Frontend verfügbar machen
		Bind: []interface{}{
			jarvisApp,
		},
		
		Windows: &windows.Options{
			WebviewIsTransparent: false,
			WindowIsTranslucent:  false,
			DisableWindowIcon:    false,
		},
	})

	if err != nil {
		log.Fatal(err)
	}
}
