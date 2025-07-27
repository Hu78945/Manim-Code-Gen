"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Play, Users } from "lucide-react"

interface CommunityVideo {
    id: number
    prompt: string
    video_url: string
    quality: string
}

interface CommunityResponse {
    data: CommunityVideo[]
}

export default function CommunityVideos() {
    const [videos, setVideos] = useState<CommunityVideo[]>([])
    const [selectedVideo, setSelectedVideo] = useState<CommunityVideo | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchCommunityVideos()
    }, [])

    const fetchCommunityVideos = async () => {
        try {
            const response = await fetch("/api/community-videos")
            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.error || "Failed to fetch videos")
            }

            const data = await response.json()
            // Handle both possible response structures
            setVideos(data.data || data)
        } catch (error) {
            console.error("Error fetching community videos:", error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                    <Card key={i} className="animate-pulse">
                        <CardContent className="p-4">
                            <div className="aspect-video bg-gray-200 rounded-lg mb-3"></div>
                            <div className="h-4 bg-gray-200 rounded mb-2"></div>
                            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        )
    }

    return (
        <>
            <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    <h2 className="text-2xl font-bold">Community Videos</h2>
                </div>
                <p className="text-gray-600">Explore videos created by our community ({videos.length} videos)</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {videos.map((video) => (
                    <Card
                        key={video.id}
                        className="cursor-pointer hover:shadow-lg transition-shadow group"
                        onClick={() => setSelectedVideo(video)}
                    >
                        <CardContent className="p-4">
                            <div className="relative aspect-video bg-gray-100 rounded-lg mb-3 overflow-hidden">
                                <video
                                    src={video.video_url}
                                    className="w-full h-full object-cover"
                                    poster="/placeholder.svg?height=200&width=300&text=Video+Thumbnail"
                                />
                                <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Play className="w-12 h-12 text-white" />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="font-medium text-sm line-clamp-2 leading-relaxed">{video.prompt}</p>
                                <div className="flex items-center justify-between">
                                    <Badge variant="secondary" className="text-xs capitalize">
                                        {video.quality} quality
                                    </Badge>
                                    <span className="text-xs text-gray-500">ID: {video.id}</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {videos.length === 0 && !loading && (
                <div className="text-center py-12">
                    <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No videos yet</h3>
                    <p className="text-gray-600">Be the first to create a video and share it with the community!</p>
                </div>
            )}

            <Dialog open={!!selectedVideo} onOpenChange={() => setSelectedVideo(null)}>
                <DialogContent className="max-w-4xl">
                    <DialogHeader>
                        <DialogTitle className="text-left">{selectedVideo?.prompt}</DialogTitle>
                    </DialogHeader>

                    {selectedVideo && (
                        <div className="space-y-4">
                            <div className="aspect-video bg-black rounded-lg overflow-hidden">
                                <video
                                    src={selectedVideo.video_url}
                                    controls
                                    autoPlay
                                    className="w-full h-full"
                                    poster="/placeholder.svg?height=400&width=600&text=Loading+Video"
                                >
                                    Your browser does not support the video tag.
                                </video>
                            </div>

                            <div className="flex items-center justify-between text-sm text-gray-600">
                                <Badge variant="outline">{selectedVideo.quality} quality</Badge>
                                <span>Video ID: {selectedVideo.id}</span>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </>
    )
}
