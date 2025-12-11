import { Calendar, Cloud, FileText, Home, Music, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuickAction {
  icon: React.ElementType;
  label: string;
}

const quickActions: QuickAction[] = [
  { icon: Home, label: "Smart Home" },
  { icon: Calendar, label: "Kalender" },
  { icon: Cloud, label: "Wetter" },
  { icon: Music, label: "Musik" },
  { icon: FileText, label: "Notizen" },
  { icon: Settings, label: "Einstellungen" },
];

interface QuickActionsProps {
  onAction?: (label: string) => void;
}

const QuickActions = ({ onAction }: QuickActionsProps) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 p-4">
      {quickActions.map((action) => {
        const Icon = action.icon;
        return (
          <Button
            key={action.label}
            variant="outline"
            className="h-20 flex flex-col gap-2"
            onClick={() => onAction?.(action.label)}
          >
            <Icon className="h-6 w-6" />
            <span className="text-xs">{action.label}</span>
          </Button>
        );
      })}
    </div>
  );
};

export default QuickActions;
