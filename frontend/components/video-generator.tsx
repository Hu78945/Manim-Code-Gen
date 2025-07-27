"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Play, AlertCircle, CheckCircle, Clock, Loader2 } from "lucide-react"

interface GenerationResponse {
    message: string
    task_id: string
    estimated_time: string
}

interface StatusResponse {
    task_id: string
    status: "queued" | "processing" | "completed" | "failed"
    video_url?: string
    error_message?: string
    attempts: number
    progress: string
}

export default function VideoGenerator() {
    const [prompt, setPrompt] = useState("")
    const [quality, setQuality] = useState<"low" | "medium" | "high">("low")
    const [isGenerating, setIsGenerating] = useState(false)
    const [taskId, setTaskId] = useState<string | null>(null)
    const [status, setStatus] = useState<StatusResponse | null>(null)
    const [progress, setProgress] = useState(0)
    const [error, setError] = useState<string | null>(null)

    const handleGenerate = async () => {
        if (!prompt.trim()) return

        setIsGenerating(true)
        setError(null)
        setStatus(null)
        setProgress(0)

        try {
            const response = await fetch("/api/generate-video", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt, quality }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.error || "Failed to start video generation")
            }

            const data: GenerationResponse = await response.json()
            setTaskId(data.task_id)

            // Start polling for status
            pollStatus(data.task_id)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to start video generation. Please try again.")
            setIsGenerating(false)
        }
    }

    const pollStatus = async (id: string) => {
        try {
            const response = await fetch(`/api/video-status/${id}`)
            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.error || "Failed to get status")
            }

            const statusData: StatusResponse = await response.json()
            setStatus(statusData)

            // Update progress based on status
            switch (statusData.status) {
                case "queued":
                    setProgress(10)
                    break
                case "processing":
                    setProgress(50)
                    break
                case "completed":
                    setProgress(100)
                    setIsGenerating(false)
                    return
                case "failed":
                    setError(statusData.error_message || "Video generation failed. Please try again.")
                    setIsGenerating(false)
                    return
            }

            // Continue polling if not completed or failed
            setTimeout(() => pollStatus(id), 60000) // Poll every minute
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to check video status. Please try again.")
            setIsGenerating(false)
        }
    }

    const getStatusIcon = () => {
        if (!status) return <Clock className="w-5 h-5 text-blue-500" />

        switch (status.status) {
            case "queued":
                return <Clock className="w-5 h-5 text-yellow-500" />
            case "processing":
                return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            case "completed":
                return <CheckCircle className="w-5 h-5 text-green-500" />
            case "failed":
                return <AlertCircle className="w-5 h-5 text-red-500" />
        }
    }

    const getStatusText = () => {
        if (!status) return "Initializing..."

        switch (status.status) {
            case "queued":
                return "Video queued for processing..."
            case "processing":
                return "Generating your video..."
            case "completed":
                return "Video generated successfully!"
            case "failed":
                return "Video generation failed"
        }
    }

    const getEstimatedTime = () => {
        switch (quality) {
            case "low":
                return "1-2 minutes"
            case "medium":
                return "2-4 minutes"
            case "high":
                return "3-6 minutes"
            default:
                return "1-3 minutes"
        }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Generate Explanation Video</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <label htmlFor="prompt" className="block text-sm font-medium mb-2">
                            Enter your prompt
                        </label>
                        <Textarea
                            id="prompt"
                            placeholder="e.g., explain me the concept of machine learning"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            rows={4}
                            disabled={isGenerating}
                        />
                    </div>

                    <div>
                        <label htmlFor="quality" className="block text-sm font-medium mb-2">
                            Video Quality
                        </label>
                        <select
                            id="quality"
                            value={quality}
                            onChange={(e) => setQuality(e.target.value as "low" | "medium" | "high")}
                            disabled={isGenerating}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="low">Low Quality (Faster)</option>
                            <option value="medium">Medium Quality</option>
                            <option value="high">High Quality (Slower)</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">Estimated time: {getEstimatedTime()}</p>
                    </div>

                    <Button onClick={handleGenerate} disabled={!prompt.trim() || isGenerating} className="w-full">
                        {isGenerating ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Generating Video...
                            </>
                        ) : (
                            <>
                                <Play className="w-4 h-4 mr-2" />
                                Generate Video
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {isGenerating && (
                <Card>
                    <CardContent className="pt-6">
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                {getStatusIcon()}
                                <span className="font-medium">{getStatusText()}</span>
                            </div>

                            <Progress value={progress} className="w-full" />

                            {status && <p className="text-sm text-gray-600">{status.progress}</p>}

                            <div className="text-sm text-gray-500 space-y-1">
                                <p>Estimated time: {getEstimatedTime()}. We&apos;ll check the status every minute.</p>
                                <p>
                                    Quality: <span className="capitalize font-medium">{quality}</span> | Max retries: 5
                                </p>
                                {taskId && (
                                    <p>
                                        Task ID: <code className="bg-gray-100 px-1 rounded text-xs">{taskId}</code>
                                    </p>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {status?.status === "completed" && status.video_url && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <CheckCircle className="w-5 h-5 text-green-500" />
                            Your Video is Ready!
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="aspect-video bg-black rounded-lg overflow-hidden">
                            <video
                                src={status.video_url}
                                controls
                                className="w-full h-full"
                                poster="/placeholder.svg?height=400&width=600&text=Video+Ready"
                            >
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div className="mt-4 space-y-2">
                            <p className="text-sm text-gray-600">
                                <strong>Prompt:</strong> {prompt}
                            </p>
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span>
                                    Quality: <span className="capitalize font-medium">{quality}</span>
                                </span>
                                <span>Attempts: {status.attempts}</span>
                                <span>
                                    Task ID: <code className="bg-gray-100 px-1 rounded text-xs">{status.task_id}</code>
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
