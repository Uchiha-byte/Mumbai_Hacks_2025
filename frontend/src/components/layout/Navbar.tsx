import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ShieldCheck, Zap, Activity } from "lucide-react"

export function Navbar() {
    return (
        <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 shadow-sm">
            <div className="container flex h-16 items-center justify-between px-4 md:px-6">
                {/* Logo Section */}
                <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
                    <img src="/favicon.ico" alt="TruthScan Logo" className="h-8 w-8" />
                    <span className="text-2xl font-bold tracking-tight text-blue-600 font-serif">
                        TruthScan
                    </span>
                </Link>

                {/* Action Buttons */}
                <div className="flex items-center gap-3">
                    <Link href="/quick-check">
                        <Button variant="outline" size="sm" className="hidden sm:flex gap-2 border-blue-200 hover:bg-blue-50 text-blue-700 hover:text-blue-800 transition-all">
                            <Zap className="h-4 w-4" />
                            Quick Check
                        </Button>
                    </Link>

                    <div className="h-6 w-px bg-border hidden sm:block" />

                    <Link href="/analyze">
                        <Button size="sm" className="gap-2 shadow-md hover:shadow-lg transition-all bg-blue-600 hover:bg-blue-700 text-white border-0">
                            <Activity className="h-4 w-4" />
                            <span className="hidden sm:inline">Deep Analysis</span>
                            <span className="sm:hidden">Analyze</span>
                        </Button>
                    </Link>
                </div>
            </div>
        </nav>
    )
}
