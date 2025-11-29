"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Navbar } from "@/components/layout/Navbar"
import { Upload, Zap, CheckCircle, XCircle, AlertCircle, Loader2, ArrowRight, FileText, ImageIcon } from "lucide-react"

type Verdict = "FAKE" | "VERIFIED" | "SUSPECT" | "MIXED"

interface QuickResult {
  verdict: Verdict
  confidence: number
  summary_one_liner: string
  tl_dr_bullets: string[]
  evidence: any[]
  reasons: string[]
}

export default function QuickCheckPage() {
  const [content, setContent] = useState("")
  const [contentType, setContentType] = useState<"text" | "image">("text")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QuickResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!content.trim()) {
      setError("Please enter some content to analyze")
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/v1/quick-analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content,
          content_type: contentType,
          metadata: {}
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze content")
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setContent(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const getVerdictColor = (verdict: Verdict) => {
    switch (verdict) {
      case "FAKE": return "text-red-600 bg-red-50 border-red-200"
      case "VERIFIED": return "text-green-600 bg-green-50 border-green-200"
      case "SUSPECT": return "text-orange-600 bg-orange-50 border-orange-200"
      case "MIXED": return "text-yellow-600 bg-yellow-50 border-yellow-200"
      default: return "text-gray-600 bg-gray-50 border-gray-200"
    }
  }

  const getVerdictIcon = (verdict: Verdict) => {
    switch (verdict) {
      case "FAKE": return <XCircle className="h-8 w-8 text-red-600" />
      case "VERIFIED": return <CheckCircle className="h-8 w-8 text-green-600" />
      case "SUSPECT": return <AlertCircle className="h-8 w-8 text-orange-600" />
      case "MIXED": return <AlertCircle className="h-8 w-8 text-yellow-600" />
    }
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />

      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center p-3 bg-yellow-100 rounded-full mb-2">
              <Zap className="h-8 w-8 text-yellow-600 fill-yellow-600" />
            </div>
            <h1 className="text-4xl font-bold tracking-tight">Quick Check</h1>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Instant misinformation detection using AI similarity matching.
              Get results in seconds.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-[1fr_350px]">
            {/* Main Input Column */}
            <div className="space-y-6">
              <Card className="border-2 shadow-sm">
                <CardHeader>
                  <CardTitle>Content to Analyze</CardTitle>
                  <CardDescription>
                    Choose content type and enter data below
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Type Selector */}
                  <div className="grid grid-cols-2 gap-4 p-1 bg-muted rounded-lg">
                    <button
                      onClick={() => setContentType("text")}
                      className={`flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-md transition-all ${contentType === "text"
                          ? "bg-background shadow-sm text-foreground"
                          : "text-muted-foreground hover:text-foreground"
                        }`}
                    >
                      <FileText className="h-4 w-4" />
                      Text Analysis
                    </button>
                    <button
                      onClick={() => setContentType("image")}
                      className={`flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-md transition-all ${contentType === "image"
                          ? "bg-background shadow-sm text-foreground"
                          : "text-muted-foreground hover:text-foreground"
                        }`}
                    >
                      <ImageIcon className="h-4 w-4" />
                      Image Forensics
                    </button>
                  </div>

                  {/* Content Input */}
                  {contentType === "text" ? (
                    <Textarea
                      placeholder="Paste the claim, headline, or text you want to verify..."
                      value={content}
                      onChange={(e) => setContent(e.target.value)}
                      className="min-h-[200px] resize-y text-base p-4"
                    />
                  ) : (
                    <div className="border-2 border-dashed border-muted-foreground/25 rounded-xl p-8 text-center hover:bg-muted/50 transition-colors">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="hidden"
                        id="image-upload"
                      />
                      <label htmlFor="image-upload" className="cursor-pointer block">
                        {content ? (
                          <div className="relative group">
                            <img
                              src={content}
                              alt="Uploaded"
                              className="max-h-[300px] mx-auto rounded-lg shadow-md"
                            />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center text-white font-medium">
                              Click to change image
                            </div>
                          </div>
                        ) : (
                          <div className="py-8">
                            <div className="bg-muted w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                              <Upload className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <h3 className="text-lg font-semibold mb-1">Upload an Image</h3>
                            <p className="text-sm text-muted-foreground">
                              Drag & drop or click to browse
                            </p>
                          </div>
                        )}
                      </label>
                    </div>
                  )}

                  {/* Submit Button */}
                  <Button
                    onClick={handleSubmit}
                    disabled={loading || !content.trim()}
                    className="w-full h-12 text-lg font-medium shadow-md hover:shadow-lg transition-all"
                    size="lg"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Analyzing Content...
                      </>
                    ) : (
                      <>
                        <Zap className="mr-2 h-5 w-5" />
                        Run Quick Check
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Error Display */}
              {error && (
                <div className="p-4 rounded-lg border border-red-200 bg-red-50 text-red-700 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                  <XCircle className="h-5 w-5 shrink-0" />
                  <p className="font-medium">{error}</p>
                </div>
              )}

              {/* Results Display */}
              {result && (
                <Card className="border-2 shadow-md animate-in fade-in slide-in-from-bottom-4 duration-500 overflow-hidden">
                  <div className={`p-6 border-b ${getVerdictColor(result.verdict).split(' ')[1]}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium uppercase tracking-wider opacity-80 mb-1">Verdict</p>
                        <div className="flex items-center gap-3">
                          {getVerdictIcon(result.verdict)}
                          <span className={`text-3xl font-bold ${getVerdictColor(result.verdict).split(' ')[0]}`}>
                            {result.verdict}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium uppercase tracking-wider opacity-80 mb-1">Confidence</p>
                        <span className="text-3xl font-bold">{result.confidence}%</span>
                      </div>
                    </div>
                  </div>

                  <CardContent className="p-6 space-y-6">
                    {/* Summary */}
                    <div className="bg-muted/50 p-4 rounded-lg border">
                      <p className="font-medium text-lg leading-relaxed">{result.summary_one_liner}</p>
                    </div>

                    {/* Key Findings */}
                    <div>
                      <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
                        <FileText className="h-5 w-5 text-primary" />
                        Key Findings
                      </h3>
                      <ul className="space-y-3">
                        {result.tl_dr_bullets.map((bullet, idx) => (
                          <li key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-background border shadow-sm">
                            <span className="text-primary mt-0.5">•</span>
                            <span className="text-foreground/90">{bullet}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Reasons */}
                    {result.reasons.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground mb-3">
                          Technical Reasoning
                        </h3>
                        <div className="bg-muted rounded-lg p-4 text-sm space-y-2 text-muted-foreground">
                          {result.reasons.map((reason, idx) => (
                            <p key={idx} className="flex items-start gap-2">
                              <ArrowRight className="h-4 w-4 mt-0.5 shrink-0 opacity-50" />
                              <span>{reason}</span>
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar Info */}
            <div className="space-y-6">
              <Card className="bg-blue-50/50 border-blue-100">
                <CardHeader>
                  <CardTitle className="text-blue-900 flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    How it works
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-blue-800 space-y-3">
                  <p>
                    <strong>Quick Check</strong> uses vector embeddings to instantly compare your content against a database of known misinformation and fact-checks.
                  </p>
                  <p>
                    For images, it performs rapid forensic analysis of metadata and compression artifacts.
                  </p>
                  <div className="pt-2 border-t border-blue-200 mt-4">
                    <p className="mb-2 font-medium">Need deeper analysis?</p>
                    <Button variant="outline" className="w-full bg-white hover:bg-blue-50 border-blue-200 text-blue-700" asChild>
                      <a href="/analyze">Try Deep Analysis</a>
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Recent Checks</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-center gap-3 text-sm border-b pb-3 last:border-0 last:pb-0">
                        <div className="h-2 w-2 rounded-full bg-gray-300" />
                        <div className="flex-1 space-y-1">
                          <div className="h-2 w-24 bg-muted rounded" />
                          <div className="h-2 w-16 bg-muted rounded" />
                        </div>
                      </div>
                    ))}
                    <p className="text-xs text-center text-muted-foreground pt-2">
                      Your recent history will appear here
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
