import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Download, X, RotateCw, Trash2 } from 'lucide-react'

interface ModelCardProps {
  modelKey: string
  model: any
  isDownloading: boolean
  downloadProgress?: any
  onDownload: (modelKey: string) => void
  onCancel: (modelKey: string) => void
  onDelete: (modelKey: string) => void
  onSelectVariant: (modelKey: string) => void
}

export const ModelCard = ({
  modelKey,
  model,
  isDownloading,
  downloadProgress,
  onDownload,
  onCancel,
  onDelete,
  onSelectVariant
}: ModelCardProps) => {
  const statusClass = isDownloading
    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    : model.downloaded
    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'

  const statusText = isDownloading
    ? 'Lädt herunter'
    : model.downloaded
    ? 'Bereit'
    : 'Nicht heruntergeladen'

  const formatNumber = (num: number) => {
    return num?.toLocaleString() || 0
  }

  const confirmDelete = () => {
    if (confirm(`${model.display_name} löschen?`)) {
      onDelete(modelKey)
    }
  }

  return (
    <Card className="p-6 hover:shadow-xl transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold">{model.display_name}</h3>
          <p className="text-sm text-muted-foreground">{model.parameters}</p>
        </div>
        <Badge className={statusClass}>{statusText}</Badge>
      </div>

      {/* Description */}
      <p className="text-sm text-muted-foreground mb-4">
        {model.description}
      </p>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-muted-foreground">Größe</div>
          <div className="text-sm font-semibold">{model.size_gb} GB</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Kontext</div>
          <div className="text-sm font-semibold">{formatNumber(model.context_length)}</div>
        </div>
      </div>

      {/* Download Progress */}
      {isDownloading && downloadProgress && (
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span>{downloadProgress?.status || 'Lädt herunter'}...</span>
            <span>{downloadProgress?.percent?.toFixed(1) || 0}%</span>
          </div>
          <Progress value={downloadProgress?.percent || 0} className="h-2" />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>{downloadProgress?.speed_mbps?.toFixed(2) || 0} MB/s</span>
            <span>ETA: {downloadProgress?.eta || 'berechne...'}</span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {!model.downloaded && !isDownloading && (
          <Button
            onClick={() => onDownload(modelKey)}
            className="flex-1"
          >
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
        )}

        {isDownloading && (
          <Button
            onClick={() => onCancel(modelKey)}
            variant="secondary"
            className="flex-1"
          >
            <X className="w-4 h-4 mr-2" />
            Abbrechen
          </Button>
        )}

        {model.downloaded && !isDownloading && (
          <>
            <Button
              onClick={() => onSelectVariant(modelKey)}
              variant="secondary"
              size="icon"
              title="Andere Variante herunterladen"
            >
              <RotateCw className="w-4 h-4" />
            </Button>

            <Button
              onClick={confirmDelete}
              variant="destructive"
              size="icon"
              title="Modell löschen"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </>
        )}
      </div>

      {/* Strengths */}
      {model.strengths && model.strengths.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <div className="text-xs text-muted-foreground mb-2">Geeignet für:</div>
          <div className="flex flex-wrap gap-2">
            {model.strengths.slice(0, 3).map((strength: string) => (
              <Badge key={strength} variant="secondary" className="text-xs">
                {strength}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
