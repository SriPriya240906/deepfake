// MOCK DATA - TO BE REMOVED WHEN BACKEND IS INTEGRATED
// This file contains mock data for frontend development only

export interface AnalysisResult {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  type: 'video-to-video' | 'photo-to-video'
  createdAt: string
  completedAt?: string
  progress: number
  
  // Input files
  referenceFile?: {
    name: string
    size: number
    type: string
  }
  targetFile: {
    name: string
    size: number
    type: string
  }
  
  // Results (only when completed)
  results?: {
    deepfakeScore: number
    totalFrames: number
    glitchFrames: number
    manipulatedRegions: Array<{
      region: string
      confidence: number
      frameIndex: number
    }>
    timeline: Array<{
      frameIndex: number
      timestamp: number
      isManipulated: boolean
      confidence: number
    }>
    evidence: Array<{
      type: 'frame_difference' | 'landmark_jump' | 'ssim_anomaly'
      frameIndex: number
      region: string
      confidence: number
      description: string
    }>
  }
}

export const mockAnalysisResult: AnalysisResult = {
  id: 'analysis_12345',
  status: 'completed',
  type: 'video-to-video',
  createdAt: '2026-09-10T14:30:00Z',
  completedAt: '2026-09-10T14:32:15Z',
  progress: 100,
  
  referenceFile: {
    name: 'original_video.mp4',
    size: 15728640, // 15MB
    type: 'video/mp4'
  },
  
  targetFile: {
    name: 'suspect_deepfake.mp4',
    size: 18874368, // 18MB
    type: 'video/mp4'
  },
  
  results: {
    deepfakeScore: 0.73,
    totalFrames: 198,
    glitchFrames: 42,
    manipulatedRegions: [
      { region: 'LEFT EYE', confidence: 0.89, frameIndex: 45 },
      { region: 'MOUTH', confidence: 0.82, frameIndex: 67 },
      { region: 'RIGHT EYE', confidence: 0.91, frameIndex: 89 },
      { region: 'NOSE', confidence: 0.76, frameIndex: 123 },
      { region: 'JAW', confidence: 0.68, frameIndex: 156 }
    ],
    timeline: Array.from({ length: 198 }, (_, i) => ({
      frameIndex: i,
      timestamp: i / 30, // 30 FPS
      isManipulated: Math.random() > 0.7,
      confidence: Math.random() * 0.4 + 0.6
    })),
    evidence: [
      {
        type: 'landmark_jump',
        frameIndex: 45,
        region: 'LEFT EYE',
        confidence: 0.89,
        description: 'Sudden landmark displacement detected in left eye region, indicating potential deepfake artifact'
      },
      {
        type: 'ssim_anomaly',
        frameIndex: 67,
        region: 'MOUTH',
        confidence: 0.82,
        description: 'Structural similarity anomaly detected in mouth region with SSIM score below threshold'
      },
      {
        type: 'frame_difference',
        frameIndex: 89,
        region: 'RIGHT EYE',
        confidence: 0.91,
        description: 'Inconsistent pixel intensity changes detected in right eye area between consecutive frames'
      }
    ]
  }
}

export const mockPhotoAnalysisResult: AnalysisResult = {
  id: 'analysis_67890',
  status: 'completed',
  type: 'photo-to-video',
  createdAt: '2026-09-10T15:00:00Z',
  completedAt: '2026-09-10T15:01:45Z',
  progress: 100,
  
  referenceFile: {
    name: 'reference_person.jpg',
    size: 2048576, // 2MB
    type: 'image/jpeg'
  },
  
  targetFile: {
    name: 'deepfake_video.mp4',
    size: 22020096, // 21MB
    type: 'video/mp4'
  },
  
  results: {
    deepfakeScore: 0.85,
    totalFrames: 277,
    glitchFrames: 63,
    manipulatedRegions: [
      { region: 'FOREHEAD', confidence: 0.94, frameIndex: 23 },
      { region: 'LEFT CHEEK', confidence: 0.87, frameIndex: 78 },
      { region: 'CHIN', confidence: 0.79, frameIndex: 134 },
      { region: 'RIGHT EYEBROW', confidence: 0.92, frameIndex: 189 },
      { region: 'NOSE', confidence: 0.83, frameIndex: 234 }
    ],
    timeline: Array.from({ length: 277 }, (_, i) => ({
      frameIndex: i,
      timestamp: i / 25, // 25 FPS
      isManipulated: Math.random() > 0.65,
      confidence: Math.random() * 0.5 + 0.5
    })),
    evidence: [
      {
        type: 'landmark_jump',
        frameIndex: 23,
        region: 'FOREHEAD',
        confidence: 0.94,
        description: 'Significant landmark displacement in forehead region suggests identity manipulation'
      },
      {
        type: 'frame_difference',
        frameIndex: 78,
        region: 'LEFT CHEEK',
        confidence: 0.87,
        description: 'Temporal inconsistency detected in left cheek area between reference photo and video frames'
      }
    ]
  }
}