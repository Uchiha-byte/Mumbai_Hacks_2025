"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, FileAudio, FileImage, FileVideo, Loader2, Type } from "lucide-react"
import { cn } from "@/lib/utils"

// Simple components for Tabs/Input/Label since we didn't create them yet
// Actually, let's just implement them inline or simple versions here to save time/files
// or I can create them properly. Let's create them properly in the next step if needed, 
// but for now I'll use standard HTML elements styled with Tailwind for the missing ones 
// to ensure it works immediately without too many file creations.

export function AnalysisForm() {
    const [contentType, setContentType] = useState("text")
    const [content, setContent] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [result, setResult] = useState<any>(null)
    const [error, setError] = useState("")

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        const reader = new FileReader()
        reader.onload = (e) => {
            const result = e.target?.result as string
            // Remove data URL prefix for the API
            // const base64 = result.split(",")[1] 
            // Actually the API might handle it or we handle it here. 
            // My previous simple frontend sent the whole thing and I handled split in backend agents?
            // Let's check backend agents... 
            // Yes, agents like image_agent.py do: if "," in image_data: image_data = image_data.split(",")[1]
            // So we can send the full data URL.
            setContent(result)
        }
        reader.readAsDataURL(file)
    }

    const analyze = async () => {
        if (!content) {
            setError("Please provide content to analyze.")
            return
        }

        setIsLoading(true)
        setError("")
        setResult(null)

        try {
            const response = await fetch("http://localhost:8000/api/v1/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content_type: contentType,
                    content: content
                })
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || "Analysis failed")
            }

            setResult(data)
        } catch (err: any) {
            setError(err.message)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="grid gap-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Button
                    variant={contentType === "text" ? "default" : "outline"}
                    onClick={() => { setContentType("text"); setContent(""); setResult(null); }}
                    className="h-24 flex flex-col gap-2"
                >
                    <Type className="h-6 w-6" />
                    Text
                </Button>
                <Button
                    variant={contentType === "image" ? "default" : "outline"}
                    onClick={() => { setContentType("image"); setContent(""); setResult(null); }}
                    className="h-24 flex flex-col gap-2"
                >
                    <FileImage className="h-6 w-6" />
                    Image
                </Button>
                <Button
                    variant={contentType === "audio" ? "default" : "outline"}
                    onClick={() => { setContentType("audio"); setContent(""); setResult(null); }}
                    className="h-24 flex flex-col gap-2"
                >
                    <FileAudio className="h-6 w-6" />
                    Audio
                </Button>
                <Button
                    variant={contentType === "video" ? "default" : "outline"}
                    onClick={() => { setContentType("video"); setContent(""); setResult(null); }}
                    className="h-24 flex flex-col gap-2"
                >
                    <FileVideo className="h-6 w-6" />
                    Video
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Input Content</CardTitle>
                    <CardDescription>
                        Provide the {contentType} content you want to verify.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {contentType === "text" ? (
                        <textarea
                            className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            placeholder="Paste the text here..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-12 hover:bg-muted/50 transition-colors">
                            <input
                                type="file"
                                accept={
                                    contentType === "image" ? "image/*" :
                                        contentType === "audio" ? "audio/*" : "video/*"
                                }
                                onChange={handleFileChange}
                                className="hidden"
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                                {contentType === "image" ? <FileImage className="h-12 w-12 text-muted-foreground" /> :
                                    contentType === "audio" ? <FileAudio className="h-12 w-12 text-muted-foreground" /> :
                                        <FileVideo className="h-12 w-12 text-muted-foreground" />}
                                <span className="text-sm font-medium text-muted-foreground">
                                    Click to upload {contentType}
                                </span>
                            </label>
                            {content && (
                                <div className="mt-4 text-xs text-primary font-medium flex items-center">
                                    <CheckCircle2 className="h-3 w-3 mr-1" /> File selected
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
                <CardFooter>
                    <Button onClick={analyze} disabled={isLoading || !content} className="w-full">
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {isLoading ? "Analyzing..." : "Analyze Content"}
                    </Button>
                </CardFooter>
            </Card>

            {error && (
                <div className="p-4 rounded-lg bg-destructive/10 text-destructive flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                </div>
            )}

            {result && (
                <Card className="border-primary/50 bg-primary/5">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-primary" />
                            Analysis Result
                        </CardTitle>
                        <CardDescription>
                            Agent Used: <span className="font-mono text-primary">{result.agent_used}</span>
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="bg-background/50 p-4 rounded-lg font-mono text-sm whitespace-pre-wrap">
                            {result.result}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}

import { ShieldCheck } from "lucide-react"
