import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AlertCircle, Home } from "lucide-react";

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="holo-panel max-w-md w-full p-8 text-center">
        <div className="flex justify-center mb-6">
          <AlertCircle className="h-20 w-20 text-primary animate-pulse" />
        </div>
        
        <h1 className="text-6xl font-display font-bold glow-text mb-4">404</h1>
        <h2 className="text-2xl font-display font-semibold mb-4">System Error</h2>
        
        <p className="text-muted-foreground mb-6">
          The requested resource could not be located in the JARVIS Core System.
        </p>
        
        <div className="flex flex-col gap-2">
          <Button onClick={() => navigate("/")} className="w-full gap-2">
            <Home className="h-4 w-4" />
            Return to Main Interface
          </Button>
          <Button variant="outline" onClick={() => window.history.back()} className="w-full">
            Go Back
          </Button>
        </div>
        
        <div className="mt-6 pt-6 border-t border-border/40">
          <p className="text-xs text-muted-foreground font-mono">
            Error Code: 404_RESOURCE_NOT_FOUND
          </p>
        </div>
      </Card>
    </div>
  );
};

export default NotFound;
