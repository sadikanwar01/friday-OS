"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FolderOpen, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";

export function FilesFeature() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
          <FolderOpen className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">File Manager</h1>
          <p className="text-sm text-muted-foreground">Manage FRIDAY OS workspaces</p>
        </div>
      </div>

      <Card className="bg-card/40 backdrop-blur-md border-border/50 border-dashed">
        <CardContent className="flex flex-col items-center justify-center p-20 text-center">
          <UploadCloud className="w-12 h-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium text-foreground">Drag and drop files here</h3>
          <p className="text-sm text-muted-foreground mb-6 mt-1 max-w-sm">
            Upload documents, images, or code files for FRIDAY to analyze and store in memory.
          </p>
          <Button variant="secondary">Browse Files</Button>
        </CardContent>
      </Card>
    </div>
  );
}
