import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { X } from 'lucide-react'

interface DownloadQueueProps {
  downloads: Record<string, any>
  onCancel: (modelKey: string) => void
}

export const DownloadQueue = ({ downloads, onCancel }: DownloadQueueProps) => {
  const downloadCount = Object.keys(downloads).length

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <Card className="fixed bottom-0 left-0 right-0 p-4 shadow-2xl border-t z-50">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">Aktive Downloads ({downloadCount})</h3>
        </div>

        <div className="space-y-2">
          {Object.entries(downloads).map(([key, progress]) => (
            <div
              key={key}
              className="flex items-center gap-4 p-3 bg-secondary/50 rounded-lg"
            >
              {/* Model Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium truncate">{key}</span>
                  <span className="text-sm text-muted-foreground">
                    {progress.percent?.toFixed(1) || 0}%
                  </span>
                </div>

                {/* Progress Bar */}
                <Progress value={progress.percent || 0} className="h-1.5 mb-1" />

                {/* Stats */}
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span>{progress.speed_mbps?.toFixed(2) || 0} MB/s</span>
                  <span>
                    {formatBytes(progress.downloaded)} / {formatBytes(progress.total)}
                  </span>
                  <span>ETA: {progress.eta || 'berechne...'}</span>
                </div>
              </div>

              {/* Cancel Button */}
              <Button
                onClick={() => onCancel(key)}
                variant="destructive"
                size="sm"
              >
                <X className="w-4 h-4 mr-1" />
                Abbrechen
              </Button>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
