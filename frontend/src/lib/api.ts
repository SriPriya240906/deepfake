/**
 * API client for communicating with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}

export interface AnalysisStartResponse {
  analysis_id: string
  status: string
  message: string
  estimated_duration?: number
}

export interface AnalysisStatusResponse {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step?: string
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`
      console.log(`API Request: ${options.method || 'GET'} ${url}`)

      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
        },
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          error: data.detail || `HTTP error ${response.status}`,
          status: response.status,
        }
      }

      return {
        data,
        status: response.status,
      }
    } catch (error) {
      console.error('API Request failed:', error)
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      }
    }
  }

  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.makeRequest('/health')
  }

  async startVideoAnalysis(
    referenceVideo: File,
    targetVideo: File,
    parameters: {
      displacement_threshold?: number
      diff_threshold?: number
      ssim_threshold?: number
    } = {}
  ): Promise<ApiResponse<AnalysisStartResponse>> {
    const formData = new FormData()
    formData.append('reference_video', referenceVideo)
    formData.append('target_video', targetVideo)
    formData.append('displacement_threshold', (parameters.displacement_threshold || 10.0).toString())
    formData.append('diff_threshold', (parameters.diff_threshold || 20).toString())
    formData.append('ssim_threshold', (parameters.ssim_threshold || 0.85).toString())

    return this.makeRequest('/api/analyze/video', {
      method: 'POST',
      body: formData,
    })
  }

  async startPhotoAnalysis(
    referencePhoto: File,
    targetVideo: File,
    parameters: {
      displacement_threshold?: number
      diff_threshold?: number
      ssim_threshold?: number
    } = {}
  ): Promise<ApiResponse<AnalysisStartResponse>> {
    const formData = new FormData()
    formData.append('reference_photo', referencePhoto)
    formData.append('target_video', targetVideo)
    formData.append('displacement_threshold', (parameters.displacement_threshold || 10.0).toString())
    formData.append('diff_threshold', (parameters.diff_threshold || 20).toString())
    formData.append('ssim_threshold', (parameters.ssim_threshold || 0.85).toString())

    return this.makeRequest('/api/analyze/photo-video', {
      method: 'POST',
      body: formData,
    })
  }

  async getAnalysisStatus(analysisId: string): Promise<ApiResponse<AnalysisStatusResponse>> {
    return this.makeRequest(`/api/analysis/${analysisId}/status`)
  }

  async getAnalysisResults(analysisId: string): Promise<ApiResponse<any>> {
    return this.makeRequest(`/api/analysis/${analysisId}`)
  }

  async listAnalyses(limit: number = 50, offset: number = 0): Promise<ApiResponse<any>> {
    return this.makeRequest(`/api/analyses?limit=${limit}&offset=${offset}`)
  }

  async deleteAnalysis(analysisId: string): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest(`/api/analysis/${analysisId}`, {
      method: 'DELETE',
    })
  }
}

export const apiClient = new ApiClient()

// Utility function to check if backend is available
export async function checkBackendConnection(): Promise<boolean> {
  try {
    const response = await apiClient.healthCheck()
    return response.status === 200
  } catch {
    return false
  }
}