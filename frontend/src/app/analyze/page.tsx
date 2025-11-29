import { Navbar } from "@/components/layout/Navbar"
import { AnalysisForm } from "@/components/analysis/AnalysisForm"

export default function AnalyzePage() {
    return (
        <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1 container py-12">
                <div className="max-w-4xl mx-auto space-y-8">
                    <div className="text-center space-y-2">
                        <h1 className="text-3xl font-bold tracking-tight">Content Analysis</h1>
                        <p className="text-muted-foreground">
                            Select the content type and upload your media for deepfake detection and forensic analysis.
                        </p>
                    </div>

                    <AnalysisForm />
                </div>
            </main>
        </div>
    )
}
