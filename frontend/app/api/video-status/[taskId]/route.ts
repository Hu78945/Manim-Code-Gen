import { type NextRequest, NextResponse } from "next/server"
import axios from "axios"

export async function GET(request: NextRequest, { params }: { params: { taskId: string } }) {
    try {
        const { taskId } = params

        // Call your actual status check API
        const response = await axios.get(`http://127.0.0.1:8000/video-status/${taskId}`, {
            headers: {
                accept: "application/json",
            },
        })

        return NextResponse.json(response.data)
    } catch (error) {
        console.error("Error checking video status:", error)

        if (axios.isAxiosError(error)) {
            const status = error.response?.status || 500
            const message = error.response?.data?.detail || "Failed to check video status"
            return NextResponse.json({ error: message }, { status })
        }

        return NextResponse.json({ error: "Failed to check video status" }, { status: 500 })
    }
}
