"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { MemoryEntry } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrainCircuit, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function MemoryFeature() {
  const { data: memories, isLoading } = useQuery({
    queryKey: ['memories'],
    queryFn: () => api.get<MemoryEntry[]>('/api/memory'),
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
          <BrainCircuit className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Memory Bank</h1>
          <p className="text-sm text-muted-foreground">Persistent knowledge and context</p>
        </div>
      </div>

      <Card className="bg-card/40 backdrop-blur-md border-border/50">
        <CardHeader>
          <CardTitle className="text-lg">Stored Context</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : !memories || memories.length === 0 ? (
            <div className="text-center p-8 text-muted-foreground">
              No memories found.
            </div>
          ) : (
            <ScrollArea className="h-[600px] pr-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {memories.map((memory) => (
                  <Card key={memory.id} className="bg-secondary/20 border-border/30">
                    <CardHeader className="py-3 px-4 flex flex-row items-center justify-between space-y-0">
                      <div className="font-medium text-sm text-primary">{memory.key}</div>
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {memory.category}
                      </Badge>
                    </CardHeader>
                    <CardContent className="px-4 pb-4">
                      <pre className="text-xs bg-black/40 p-3 rounded-md overflow-x-auto text-muted-foreground border border-white/5">
                        {typeof memory.value === 'object' 
                          ? JSON.stringify(memory.value, null, 2) 
                          : String(memory.value)}
                      </pre>
                      <div className="flex justify-between items-center mt-3 text-[10px] text-muted-foreground/50">
                        <span>Importance: {memory.importance}/10</span>
                        <span>{new Date(memory.created_at).toLocaleString()}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
