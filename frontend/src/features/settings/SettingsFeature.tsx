"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Settings, Monitor, Mic, Code2, Database } from "lucide-react";
import { Switch } from "@/components/ui/switch";

export function SettingsFeature() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
          <Settings className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
          <p className="text-sm text-muted-foreground">Configure FRIDAY OS preferences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card/40 backdrop-blur-md border-border/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><Monitor className="w-4 h-4" /> Appearance</CardTitle>
            <CardDescription>Customize the interface</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Dark Mode</p>
                <p className="text-xs text-muted-foreground">Force dark mode always on</p>
              </div>
              <Switch checked={true} disabled />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Glassmorphism</p>
                <p className="text-xs text-muted-foreground">Enable blur effects</p>
              </div>
              <Switch checked={true} disabled />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/40 backdrop-blur-md border-border/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><Mic className="w-4 h-4" /> Voice Engine</CardTitle>
            <CardDescription>Configure speech processing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Push to Talk</p>
                <p className="text-xs text-muted-foreground">Manual voice activation</p>
              </div>
              <Switch checked={true} disabled />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Continuous Listening</p>
                <p className="text-xs text-muted-foreground">Wake word activation</p>
              </div>
              <Switch checked={false} disabled />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/40 backdrop-blur-md border-border/50 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><Code2 className="w-4 h-4" /> Developer</CardTitle>
            <CardDescription>Advanced system configuration</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">API Base URL</p>
                <p className="text-xs text-muted-foreground font-mono">{process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Debug Logging</p>
                <p className="text-xs text-muted-foreground">Show detailed console output</p>
              </div>
              <Switch checked={true} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
