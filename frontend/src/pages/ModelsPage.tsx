import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { ModelCard } from '@/components/models/ModelCard'
import { VariantDialog } from '@/components/models/VariantDialog'
import { DownloadQueue } from '@/components/models/DownloadQueue'
import { useModels } from '@/hooks/useModels'

const ModelsPage = () => {
  const {
    models,
    activeDownloads,
    loadModels,
    startDownload,
    cancelDownload,
    deleteModel,
    getVariants
  } = useModels()

  const [variantDialogOpen, setVariantDialogOpen] = useState(false)
  const [selectedModelKey, setSelectedModelKey] = useState('')
  const [modelVariants, setModelVariants] = useState<any[]>([])

  const hasActiveDownloads = Object.keys(activeDownloads).length > 0

  const isDownloading = (modelKey: string) => {
    return modelKey in activeDownloads
  }

  const getProgress = (modelKey: string) => {
    return activeDownloads[modelKey]
  }

  const showVariantDialog = async (modelKey: string) => {
    setSelectedModelKey(modelKey)
    const variants = await getVariants(modelKey)
    setModelVariants(variants)
    setVariantDialogOpen(true)
  }

  const downloadVariant = (variant: any) => {
    startDownload(selectedModelKey, variant.quantization)
    setVariantDialogOpen(false)
  }

  useEffect(() => {
    loadModels()
  }, [])

  return (
    <div className="models-page p-6">
      <div className="header mb-6">
        <h1 className="text-3xl font-bold mb-2">LLM Modelle</h1>
        <p className="text-gray-600 dark:text-gray-400">Sprachmodelle herunterladen und verwalten</p>
      </div>

      {/* Model Grid */}
      {Object.keys(models).length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(models).map(([key, model]) => (
            <ModelCard
              key={key}
              modelKey={key}
              model={model}
              isDownloading={isDownloading(key)}
              downloadProgress={getProgress(key)}
              onDownload={startDownload}
              onCancel={cancelDownload}
              onDelete={deleteModel}
              onSelectVariant={showVariantDialog}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Lade Modelle...</p>
        </div>
      )}

      {/* Variant Selection Dialog */}
      {variantDialogOpen && (
        <VariantDialog
          modelKey={selectedModelKey}
          variants={modelVariants}
          onSelect={downloadVariant}
          onClose={() => setVariantDialogOpen(false)}
        />
      )}

      {/* Download Queue (Sticky Bottom) */}
      {hasActiveDownloads && (
        <DownloadQueue
          downloads={activeDownloads}
          onCancel={cancelDownload}
        />
      )}
    </div>
  )
}

export default ModelsPage
