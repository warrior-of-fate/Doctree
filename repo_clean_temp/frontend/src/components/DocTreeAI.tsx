"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import {
  Upload,
  FileText,
  Download,
  ChevronRight,
  ChevronDown,
  Sun,
  Moon,
  Copy,
  Check,
} from "lucide-react";

// Document section shape
interface Section {
  id: string;
  title: string;
  pageNumber: number;
  content: string;
  children?: Section[];
}

// ========== Backend integration ==========
const API_BASE_URL = "http://localhost:8000"; // FastAPI

async function uploadPdfAndGetHierarchy(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/extract`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let text = await res.text().catch(() => "");
    try {
      const json = JSON.parse(text);
      throw new Error(json.detail || `API error ${res.status}`);
    } catch {
      throw new Error(`API error: ${res.status}`);
    }
  }

  const data = await res.json();

  if (!data.ok || !data.hierarchy) {
    throw new Error("Invalid response from backend");
  }

  return data.hierarchy;
}

function mapBackendToSectionTree(hierarchy: any): Section {
  let idCounter = 0;
  const makeId = () => `sec-${idCounter++}`;

  const mapSection = (sec: any): Section => ({
    id: makeId(),
    title: sec.title || "Untitled",
    pageNumber: sec.pageNumber || 1,
    content: Array.isArray(sec.content) ? sec.content.join("\n\n") : sec.content || "",
    children: (sec.children || []).map(mapSection),
  });

  return {
    id: "root",
    title: hierarchy.metadata?.source_file || "Document",
    pageNumber: 1,
    content: "",
    children: (hierarchy.sections || []).map(mapSection),
  };
}
// ========== End backend integration ==========

export default function DocTreeAI() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [hierarchyData, setHierarchyData] = useState<Section | null>(null);
  const [jsonOutput, setJsonOutput] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"tree" | "json">("tree");
  const [darkMode, setDarkMode] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(["root"]));
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (file: File) => {
    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file");
      return;
    }
    if (file.size > 500 * 1024 * 1024) {
      setError("File size exceeds 500MB limit");
      return;
    }
    setUploadedFile(file);
    setError(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleProcessDocument = async () => {
    if (!uploadedFile) {
      setError("Please upload a file first");
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setError(null);
    setHierarchyData(null);
    setJsonOutput(null);

    try {
      setProgress(10);
      const backendHierarchy = await uploadPdfAndGetHierarchy(uploadedFile);
      setProgress(70);
      const sectionTree = mapBackendToSectionTree(backendHierarchy);
      setHierarchyData(sectionTree);
      setJsonOutput(JSON.stringify(backendHierarchy, null, 2));
      setProgress(100);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to process document");
      setProgress(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleNode = (id: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      return newSet;
    });
  };

  const downloadJSON = () => {
    if (!jsonOutput) return;
    const blob = new Blob([jsonOutput], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "document-hierarchy.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!jsonOutput) return;
    navigator.clipboard.writeText(jsonOutput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const TreeNode = ({ node }: { node: Section }) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(node.id);
    return (
      <div className="ml-4 my-1">
        <div
          className="flex items-center py-2 px-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
          onClick={() => hasChildren && toggleNode(node.id)}
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="h-4 w-4 mr-1 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 mr-1 text-muted-foreground" />
            )
          ) : (
            <div className="w-5" />
          )}

          <span className="font-medium text-foreground flex-1">{node.title}</span>

          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">p.{node.pageNumber}</span>
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l-2 border-border ml-3 pl-2">
            {node.children?.map((child) => (
              <TreeNode key={child.id} node={child} />
            ))}
          </div>
        )}

        {isExpanded && (
          <div className="ml-8 mt-2 mb-4 p-3 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground">{node.content}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`min-h-screen ${darkMode ? "dark bg-gray-900" : "bg-gray-50"}`}>
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="flex justify-between items-center mb-12">
          <div className="flex items-center space-x-2">
            <div className="bg-primary w-10 h-10 rounded-lg flex items-center justify-center">
              <FileText className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">DocTree.AI</h1>
          </div>

          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="icon" onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>

            <Button variant="outline" asChild>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer">
                GitHub
              </a>
            </Button>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <Card className="border border-border">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="mr-2 h-5 w-5" />
                Upload Document
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                  error ? "border-destructive bg-destructive/10" : "border-border hover:border-primary"
                }`}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input type="file" ref={fileInputRef} className="hidden" accept=".pdf" onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])} />

                <div className="flex flex-col items-center justify-center space-y-3">
                  <Upload className="h-10 w-10 text-muted-foreground" />
                  <div>
                    <p className="font-medium text-foreground">{uploadedFile ? uploadedFile.name : "Drag & drop your PDF here"}</p>
                      <p className="text-sm text-muted-foreground mt-1">{uploadedFile ? `${(uploadedFile.size / 1024 / 1024).toFixed(2)} MB` : "PDF files only (max 500MB)"}</p>
                  </div>
                  <Button variant="secondary">Browse Files</Button>
                </div>
              </div>

              {error && <div className="text-destructive text-sm py-2 px-4 bg-destructive/10 rounded-lg">{error}</div>}

              <Button className="w-full" onClick={handleProcessDocument} disabled={isProcessing || !uploadedFile}>
                {isProcessing ? "Processing..." : "Process Document"}
              </Button>

              {isProcessing && (
                <div className="space-y-2">
                  <Progress value={progress} className="w-full" />
                  <p className="text-center text-sm text-muted-foreground">Analyzing document structure... {progress}%</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results Section */}
          <Card className="border border-border">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-center">
                <CardTitle>Document Hierarchy</CardTitle>
                <div className="flex space-x-2">
                  <Button variant={activeTab === "tree" ? "default" : "outline"} size="sm" onClick={() => setActiveTab("tree")}>Tree View</Button>
                  <Button variant={activeTab === "json" ? "default" : "outline"} size="sm" onClick={() => setActiveTab("json")}>JSON Output</Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {hierarchyData ? (
                activeTab === "tree" ? (
                  <div className="p-6 max-h-[500px] overflow-y-auto">
                    <TreeNode node={hierarchyData} />
                  </div>
                ) : (
                  <div className="p-4">
                    <div className="flex justify-end mb-2">
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline" onClick={copyToClipboard}>
                          {copied ? <Check className="h-4 w-4 mr-1" /> : <Copy className="h-4 w-4 mr-1" />}
                          {copied ? "Copied!" : "Copy"}
                        </Button>
                        <Button size="sm" onClick={downloadJSON}>
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </Button>
                      </div>
                    </div>
                    <Textarea value={jsonOutput || ""} readOnly className="font-mono text-sm h-[400px] resize-none" />
                  </div>
                )
              ) : (
                <div className="p-12 text-center">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-foreground mb-1">No Document Processed</h3>
                  <p className="text-muted-foreground">Upload and process a PDF to see its hierarchical structure</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Features Section */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-center mb-12 text-foreground">How DocTree.AI Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { title: "Upload Document", description: "Drag and drop your PDF file or browse your device", icon: <Upload className="h-6 w-6" /> },
              { title: "AI Analysis", description: "Our system analyzes the document structure and content", icon: <FileText className="h-6 w-6" /> },
              { title: "Visual Hierarchy", description: "Explore the document structure in an interactive tree view", icon: <ChevronDown className="h-6 w-6" /> },
            ].map((feature, index) => (
              <Card key={index} className="border border-border">
                <CardContent className="p-6 text-center">
                  <div className="bg-primary/10 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">{feature.icon}</div>
                  <h3 className="font-semibold text-lg mb-2 text-foreground">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <footer className="mt-16 pt-8 border-t border-border text-center text-muted-foreground text-sm">
          <p>© {new Date().getFullYear()} DocTree.AI. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
}
