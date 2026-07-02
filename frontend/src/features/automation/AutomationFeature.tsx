"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AutomationTask } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Cpu, Loader2, CheckCircle2, Clock, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function AutomationFeature() {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['automation-history'],
    queryFn: () => api.get<AutomationTask[]>('/api/automation/history'),
    refetchInterval: 10000
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
          <Cpu className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Automation Engine</h1>
          <p className="text-sm text-muted-foreground">Execution timeline and history</p>
        </div>
      </div>

      <Card className="bg-card/40 backdrop-blur-md border-border/50">
        <CardHeader>
          <CardTitle className="text-lg">Recent Executions</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : !tasks || tasks.length === 0 ? (
            <div className="text-center p-12 border border-dashed border-border/50 rounded-xl">
              <Cpu className="w-10 h-10 mx-auto text-muted-foreground/30 mb-3" />
              <h3 className="text-lg font-medium text-foreground">No automations yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-1">
                Ask FRIDAY to perform a task to see it appear in the execution timeline.
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
                {tasks.map((task) => (
                  <div key={task.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-background bg-card shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 relative z-10">
                      {task.status === 'completed' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      ) : task.status === 'failed' ? (
                        <XCircle className="w-5 h-5 text-red-500" />
                      ) : (
                        <Clock className="w-5 h-5 text-amber-500" />
                      )}
                    </div>
                    
                    <Card className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-card/60 border-border/40 hover:border-primary/50 transition-colors shadow-sm">
                      <CardHeader className="p-4 pb-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground font-mono">ID: {task.id.slice(0, 8)}</span>
                          <Badge variant="outline" className={
                            task.status === 'completed' ? 'text-green-500 border-green-500/20 bg-green-500/10' :
                            task.status === 'failed' ? 'text-red-500 border-red-500/20 bg-red-500/10' :
                            'text-amber-500 border-amber-500/20 bg-amber-500/10'
                          }>
                            {task.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="p-4 pt-2">
                        <p className="text-sm font-medium leading-relaxed">{task.goal}</p>
                        <div className="text-[10px] text-muted-foreground mt-3 text-right">
                          {new Date(task.created_at).toLocaleString()}
                        </div>
                      </CardContent>
                    </Card>
                    
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
