"use client"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import VideoGenerator from "@/components/video-generator"
import CommunityVideos from "@/components/community-videos"
import { Video, Sparkles } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">AI Video Generator</h1>
          <p className="text-lg text-gray-600">Create educational explanation videos with AI</p>
        </div>

        <Tabs defaultValue="generate" className="w-full max-w-6xl mx-auto">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="generate" className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Generate Video
            </TabsTrigger>
            <TabsTrigger value="community" className="flex items-center gap-2">
              <Video className="w-4 h-4" />
              Community Videos
            </TabsTrigger>
          </TabsList>

          <TabsContent value="generate">
            <VideoGenerator />
          </TabsContent>

          <TabsContent value="community">
            <CommunityVideos />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
