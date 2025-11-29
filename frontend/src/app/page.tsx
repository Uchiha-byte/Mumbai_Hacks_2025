import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Navbar } from "@/components/layout/Navbar"
import { Shield, Search, Lock, Zap, CheckCircle2, ArrowRight, BarChart3, AudioWaveform, AlertTriangle, BrainCircuit, Newspaper } from "lucide-react"
import DotGrid from "@/components/ui/DotGrid"
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/ui/ScrollReveal"

export default function Home() {
    return (
        <div className="flex min-h-screen flex-col bg-background">
            <Navbar />

            <main className="flex-1">
                {/* Hero Section */}
                <section className="relative overflow-hidden py-20 md:py-32 lg:py-40">
                    {/* Background Elements */}
                    <div className="absolute inset-0 z-0">
                        <DotGrid
                            dotSize={2}
                            gap={20}
                            baseColor="#e5e7eb"
                            activeColor="#3b82f6"
                            proximity={100}
                            shockRadius={150}
                            shockStrength={3}
                            resistance={500}
                            returnDuration={1}
                        />
                        <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-transparent to-background pointer-events-none" />
                    </div>

                    <div className="container relative z-10 flex flex-col items-center text-center px-4 md:px-6 pointer-events-none">
                        <ScrollReveal width="100%" className="flex flex-col items-center">
                            <div className="pointer-events-auto inline-flex items-center rounded-full border bg-background/80 px-4 py-1.5 text-sm font-medium backdrop-blur-sm shadow-sm mb-8">
                                <span className="flex h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
                                AI-Powered Content Verification System
                            </div>
                        </ScrollReveal>

                        <ScrollReveal delay={0.2} width="100%" className="flex justify-center">
                            <h1 className="pointer-events-auto text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl max-w-5xl text-foreground mb-6 font-serif">
                                Verify Reality in the <br className="hidden sm:block" />
                                <span className="text-blue-600">Age of AI</span>
                            </h1>
                        </ScrollReveal>

                        <ScrollReveal delay={0.4} width="100%" className="flex justify-center">
                            <p className="pointer-events-auto max-w-[42rem] leading-relaxed text-muted-foreground sm:text-xl sm:leading-8 mb-10">
                                TruthScan uses advanced multi-modal AI agents to detect deepfakes, synthetic text, and manipulated media with enterprise-grade accuracy.
                            </p>
                        </ScrollReveal>

                        <ScrollReveal delay={0.6} width="100%" className="flex justify-center">
                            <div className="pointer-events-auto flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                                <Link href="/quick-check" className="w-full sm:w-auto">
                                    <Button size="lg" className="w-full h-14 px-8 text-lg gap-2 shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 bg-white text-black hover:bg-gray-100 border border-gray-200">
                                        <Zap className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                                        Quick Check
                                    </Button>
                                </Link>
                                <Link href="/analyze" className="w-full sm:w-auto">
                                    <Button size="lg" className="w-full h-14 px-8 text-lg gap-2 shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 bg-blue-600 hover:bg-blue-700 text-white border-0">
                                        Deep Analysis <ArrowRight className="h-5 w-5" />
                                    </Button>
                                </Link>
                            </div>
                        </ScrollReveal>

                        <ScrollReveal delay={0.8} width="100%" className="flex justify-center">
                            <div className="pointer-events-auto mt-12 flex flex-wrap justify-center items-center gap-8 text-sm text-muted-foreground">
                                <div className="flex items-center gap-2">
                                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    <span>99.8% Accuracy</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    <span>Real-time Analysis</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    <span>Secure & Private</span>
                                </div>
                            </div>
                        </ScrollReveal>
                    </div>
                </section>

                {/* Features Grid */}
                <section id="features" className="container py-20 md:py-32 px-4 md:px-6">
                    <ScrollReveal className="text-center mb-16 mx-auto" width="100%">
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl mb-4 font-serif">
                            Comprehensive Detection Suite
                        </h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                            Our multi-agent system analyzes content across all formats to identify manipulation and synthetic generation.
                        </p>
                    </ScrollReveal>

                    <StaggerContainer className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
                        <StaggerItem>
                            <FeatureCard
                                icon={<Shield className="h-10 w-10 text-blue-600" />}
                                title="Deepfake Detection"
                                description="Analyze videos and images for GAN artifacts, inconsistent lighting, and facial manipulation traces."
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <FeatureCard
                                icon={<Search className="h-10 w-10 text-blue-600" />}
                                title="Text Forensics"
                                description="Identify AI-generated text from GPT-4, Gemini, and other LLMs using linguistic pattern analysis."
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <FeatureCard
                                icon={<AudioWaveform className="h-10 w-10 text-blue-600" />}
                                title="Audio Verification"
                                description="Detect voice cloning and synthetic speech patterns in audio files with spectral analysis."
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <FeatureCard
                                icon={<BarChart3 className="h-10 w-10 text-blue-600" />}
                                title="Detailed Analytics"
                                description="Get comprehensive reports with confidence scores, key indicators, and explainable AI reasoning."
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <FeatureCard
                                icon={<Zap className="h-10 w-10 text-blue-600" />}
                                title="Real-time Processing"
                                description="Instant analysis for time-sensitive content verification with our optimized inference engine."
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <FeatureCard
                                icon={<Lock className="h-10 w-10 text-blue-600" />}
                                title="Enterprise Security"
                                description="Bank-grade encryption and privacy-first architecture ensures your data remains secure."
                            />
                        </StaggerItem>
                    </StaggerContainer>
                </section>

                {/* Age of AI Section */}
                <section className="bg-muted/30 py-20 md:py-32">
                    <div className="container px-4 md:px-6">
                        <div className="grid gap-12 lg:grid-cols-2 items-center">
                            <ScrollReveal direction="right">
                                <div className="space-y-6">
                                    <div className="inline-flex items-center rounded-full border bg-blue-50 px-3 py-1 text-sm font-medium text-blue-600">
                                        <BrainCircuit className="mr-2 h-4 w-4" />
                                        The Generative Era
                                    </div>
                                    <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl font-serif">
                                        Navigating the Age of AI
                                    </h2>
                                    <p className="text-lg text-muted-foreground leading-relaxed">
                                        As generative AI becomes more accessible, the line between reality and fabrication blurs.
                                        Tools like Midjourney, Sora, and ElevenLabs can create hyper-realistic content in seconds,
                                        making traditional verification methods obsolete.
                                    </p>
                                    <p className="text-lg text-muted-foreground leading-relaxed">
                                        TruthScan bridges this gap by deploying adversarial AI models trained to spot the
                                        subtle imperfections that human eyes miss from pixel-level inconsistencies to
                                        unnatural semantic patterns.
                                    </p>
                                </div>
                            </ScrollReveal>
                            <ScrollReveal direction="left">
                                <div className="relative w-full h-full min-h-[400px] rounded-2xl overflow-hidden border bg-background shadow-xl">
                                    <Image
                                        src="/AI.png"
                                        alt="AI Detection Active"
                                        fill
                                        className="object-cover"
                                    />
                                </div>
                            </ScrollReveal>
                        </div>
                    </div>
                </section>

                {/* Real World Impact Section */}
                <section className="container py-20 md:py-32 px-4 md:px-6">
                    <ScrollReveal className="text-center mb-16 mx-auto" width="100%">
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl mb-4 font-serif">
                            Real-World Impact
                        </h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                            Misinformation spreads 6x faster than truth. Here's what we're fighting against.
                        </p>
                    </ScrollReveal>

                    <StaggerContainer className="grid gap-8 md:grid-cols-3">
                        <StaggerItem>
                            <ImpactCard
                                icon={<AlertTriangle className="h-8 w-8 text-orange-500" />}
                                title="Election Interference"
                                description="Deepfake audio and video used to manipulate voter opinion and impersonate political candidates."
                                stat="40% increase in 2024"
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <ImpactCard
                                icon={<Newspaper className="h-8 w-8 text-blue-500" />}
                                title="Financial Fraud"
                                description="Synthetic voice attacks used to bypass biometric security and authorize fraudulent transactions."
                                stat="$11B projected losses"
                            />
                        </StaggerItem>
                        <StaggerItem>
                            <ImpactCard
                                icon={<Shield className="h-8 w-8 text-red-500" />}
                                title="Reputation Damage"
                                description="Fabricated imagery designed to harass individuals or damage corporate brand reputation."
                                stat="Instant viral spread"
                            />
                        </StaggerItem>
                    </StaggerContainer>
                </section>

                {/* Stats Section */}
                <section className="border-t bg-muted/40 py-20">
                    <div className="container px-4 md:px-6">
                        <StaggerContainer className="grid gap-8 md:grid-cols-2 lg:grid-cols-4 text-center">
                            <StaggerItem><StatCard value="99.8%" label="Detection Accuracy" /></StaggerItem>
                            <StaggerItem><StatCard value="4" label="Specialized Agents" /></StaggerItem>
                            <StaggerItem><StatCard value="<2s" label="Analysis Speed" /></StaggerItem>
                            <StaggerItem><StatCard value="24/7" label="Automated Monitoring" /></StaggerItem>
                        </StaggerContainer>
                    </div>
                </section>
            </main>

            <footer className="border-t py-8 bg-background">
                <div className="container flex flex-col items-center justify-between gap-4 md:flex-row px-4 md:px-6">
                    <p className="text-center text-sm text-muted-foreground md:text-left">
                        © 2024 TruthScan. Built by <span className="font-medium text-foreground">Uchiha_Byte</span>.
                    </p>
                    <div className="flex gap-6 text-sm text-muted-foreground">
                        <Link href="#" className="hover:text-foreground transition-colors">Privacy</Link>
                        <Link href="#" className="hover:text-foreground transition-colors">Terms</Link>
                        <Link href="#" className="hover:text-foreground transition-colors">Contact</Link>
                    </div>
                </div>
            </footer>
        </div>
    )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
    return (
        <div className="group relative overflow-hidden rounded-2xl border bg-background p-8 hover:shadow-lg transition-all hover:-translate-y-1 h-full">
            <div className="absolute inset-0 bg-blue-50 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10 flex flex-col h-full">
                <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-xl bg-blue-50 group-hover:bg-white group-hover:shadow-sm transition-colors">
                    {icon}
                </div>
                <h3 className="text-xl font-bold mb-3">{title}</h3>
                <p className="text-muted-foreground leading-relaxed">
                    {description}
                </p>
            </div>
        </div>
    )
}

function ImpactCard({ icon, title, description, stat }: { icon: React.ReactNode, title: string, description: string, stat: string }) {
    return (
        <div className="flex flex-col h-full rounded-2xl border bg-background p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="mb-4">{icon}</div>
            <h3 className="text-xl font-bold mb-2">{title}</h3>
            <p className="text-muted-foreground mb-4 flex-grow">{description}</p>
            <div className="mt-auto pt-4 border-t">
                <span className="text-sm font-semibold text-blue-600">{stat}</span>
            </div>
        </div>
    )
}

function StatCard({ value, label }: { value: string, label: string }) {
    return (
        <div className="space-y-2 p-6 rounded-xl bg-background border shadow-sm h-full flex flex-col justify-center">
            <h3 className="text-4xl font-extrabold text-blue-600">{value}</h3>
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">{label}</p>
        </div>
    )
}
