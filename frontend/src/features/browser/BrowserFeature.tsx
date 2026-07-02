"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Globe, Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function BrowserFeature() {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const handleBrowse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setIsLoading(true);
    setResult(null);
    try {
      // Assuming a generic payload based on backend structure
      const res = await api.post<Record<string, unknown>>('/api/browser', { 
        action: 'navigate',
        url: url.startsWith('http') ? url : `https://${url}` 
      });
      setResult(res);
    } catch (error: unknown) {
      setResult({ error: (error as Error).message || 'An error occurred' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
          <Globe className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Browser Agent</h1>
          <p className="text-sm text-muted-foreground">Headless web interaction</p>
        </div>
      </div>

      <Card className="bg-card/40 backdrop-blur-md border-border/50">
        <CardHeader>
          <CardTitle className="text-lg">Instruct Browser</CardTitle>
          <CardDescription>Enter a URL or a search query to execute a browser automation task.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleBrowse} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com or 'Search for AI news'" 
                className="pl-9 bg-secondary/50 border-border/50"
              />
            </div>
            <Button type="submit" disabled={isLoading || !url}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Globe className="w-4 h-4 mr-2" />}
              {isLoading ? "Executing..." : "Run"}
            </Button>
          </form>

          {result && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-2">Execution Result</h3>
              <pre className="bg-black/50 p-4 rounded-lg overflow-x-auto text-xs text-muted-foreground border border-border/50">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
