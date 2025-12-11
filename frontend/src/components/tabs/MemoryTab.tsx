import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, Trash2, Search, Clock, Database, Timer, Sparkles, Construction } from "lucide-react";
import { Input } from "@/components/ui/input";

const MemoryTab = () => {
  return (
    <div className="p-4 space-y-4">
      <Card className="border-yellow-500/50 bg-yellow-500/10">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <Construction className="h-5 w-5 text-yellow-500" />
            <p className="text-sm">Memory management features are currently being developed. Preview mode available.</p>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="short-term" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="short-term">
            <Clock className="h-4 w-4 mr-2" />
            Short-term
          </TabsTrigger>
          <TabsTrigger value="long-term">
            <Database className="h-4 w-4 mr-2" />
            Long-term
          </TabsTrigger>
          <TabsTrigger value="semantic">
            <Sparkles className="h-4 w-4 mr-2" />
            Semantic
          </TabsTrigger>
        </TabsList>

        <TabsContent value="short-term" className="space-y-4">
          <div className="flex gap-2">
            <Input placeholder="Search memory..." />
            <Button variant="outline">
              <Search className="h-4 w-4" />
            </Button>
            <Button variant="outline">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="destructive">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center justify-between">
                    <span>Memory Entry {i}</span>
                    <span className="text-xs text-muted-foreground">2 minutes ago</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">{"memory".content}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="long-term" className="space-y-4">
          <Card>
            <CardContent className="pt-6 text-center text-muted-foreground">
              <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Long-term memory storage coming soon</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="semantic" className="space-y-4">
          <Card>
            <CardContent className="pt-6 text-center text-muted-foreground">
              <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Vector memory search coming soon</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MemoryTab;
