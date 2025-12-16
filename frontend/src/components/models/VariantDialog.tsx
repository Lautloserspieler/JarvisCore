import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { X } from 'lucide-react'

interface VariantDialogProps {
  modelKey: string
  variants: any[]
  onSelect: (variant: any) => void
  onClose: () => void
}

export const VariantDialog = ({ modelKey, variants, onSelect, onClose }: VariantDialogProps) => {
  const getQualityLabel = (quant: string) => {
    const labels: Record<string, string> = {
      'Q4_K_M': 'Ausgewogen',
      'Q4_K_S': 'Schnell & Klein',
      'Q5_K_M': 'Hohe Qualität',
      'Q6_K': 'Sehr hohe Qualität',
      'Q8_0': 'Maximale Qualität'
    }
    return labels[quant] || 'Benutzerdefiniert'
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <Card
        className="p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold mb-2">Modellvariante auswählen</h2>
            <p className="text-sm text-muted-foreground">
              Wähle eine Quantisierung für {modelKey}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-3">
          {variants.map((variant) => (
            <div
              key={variant.quantization}
              className="p-4 border-2 rounded-lg hover:border-primary cursor-pointer transition-colors"
              onClick={() => onSelect(variant)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-lg">{variant.quantization}</div>
                  <div className="text-sm text-muted-foreground">{variant.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-primary">
                    {variant.size_estimate}
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {getQualityLabel(variant.quantization)}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <Button variant="secondary" onClick={onClose}>
            Abbrechen
          </Button>
        </div>
      </Card>
    </div>
  )
}
