'use client'

import { useState, useEffect } from 'react'
import { 
  Loader2, 
  FileVideo, 
  Image as ImageIcon, 
  CheckCircle2, 
  Eye, 
  Brain, 
  Search, 
  BarChart3,
  Shield
} from 'lucide-react'
import { formatBytes } from '@/lib/utils'

interface ProcessingStateProps {
  mode: 'video' | 'photo'
  analysisId: string
  files: {
    reference?: File
    target?: File
  }
}

interface ProcessingStep {
  id: string
  label: string
  description: string
  icon: React.ReactNode
  duration: number // seconds
}

const processingSteps: ProcessingStep[] = [
  {
    id: 'extract',
    label: 'Extracting Frames',
    description: 'Decoding video files and extracting individual frames for analysis',
    icon: <FileVideo className="h-5 w-5" />,
    duration: 15
  },
  {
    id: 'landmarks',
    label: 'Detecting Facial Landmarks',
    description: 'Identifying 468 facial landmarks using MediaPipe Face Mesh',
    icon: <Eye className="h-5 w-5" />,
    duration: 20
  },
  {
    id: 'tracking',
    label: 'Tracking Landmark Failures',
    description: 'Analyzing landmark displacement and identifying glitch frames',
    icon: <Brain className="h-5 w-5" />,
    duration: 10
  },
  {
    id: 'artifacts',
    label: 'Detecting Visual Artifacts',
    description: 'Comparing frames using SSIM and pixel difference analysis',
    icon: <Search className="h-5 w-5" />,
    duration: 25
  },
  {
    id: 'fragments',
    label: 'Extracting Fragments',
    description: 'Isolating inconsistent regions from detected artifact areas',
    icon: <BarChart3 className="h-5 w-5" />,
    duration: 8
  },
  {
    id: 'analysis',
    label: 'Generating Report',
    description: 'Computing deepfake score and compiling forensic evidence',
    icon: <Shield className="h-5 w-5" />,
    duration: 7
  }
]

export default function ProcessingState({ mode, analysisId, files }: ProcessingStateProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [timeElapsed, setTimeElapsed] = useState(0)

  useEffect(() => {
    const totalDuration = processingSteps.reduce((sum, step) => sum + step.duration, 0)
    let elapsed = 0

    const interval = setInterval(() => {
      elapsed += 0.1
      setTimeElapsed(elapsed)

      // Calculate which step we're in and progress
      let accumulatedTime = 0
      let stepIndex = 0
      
      for (let i = 0; i < processingSteps.length; i++) {
        accumulatedTime += processingSteps[i].duration
        if (elapsed < accumulatedTime) {
          stepIndex = i
          break
        }
        stepIndex = processingSteps.length - 1
      }

      setCurrentStep(stepIndex)
      setProgress((elapsed / totalDuration) * 100)

      if (elapsed >= totalDuration) {
        clearInterval(interval)
      }
    }, 100)

    return () => clearInterval(interval)
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex items-center justify-center w-20 h-20 mx-auto mb-6 bg-cyan-500 rounded-full">
          <Loader2 className="h-10 w-10 text-white animate-spin" />
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Forensic Analysis in Progress
        </h1>
        <p className="text-xl text-slate-600">
          {mode === 'video' 
            ? 'Comparing videos and analyzing temporal inconsistencies'
            : 'Verifying identity and detecting manipulation artifacts'
          }
        </p>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="text-lg font-semibold text-slate-900">
            Analysis Progress
          </div>
          <div className="text-sm text-slate-600">
            {formatTime(timeElapsed)} elapsed • {Math.round(progress)}% complete
          </div>
        </div>
        
        <div className="w-full bg-slate-200 rounded-full h-3 mb-4">
          <div 
            className="bg-gradient-to-r from-cyan-500 to-blue-500 h-3 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <div className="text-center">
          <div className="text-sm font-medium text-slate-700">
            {processingSteps[currentStep]?.label}
          </div>
          <div className="text-sm text-slate-600 mt-1">
            {processingSteps[currentStep]?.description}
          </div>
        </div>
      </div>

      {/* File Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {files.reference && (
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-3">
              {mode === 'video' ? (
                <FileVideo className="h-6 w-6 text-slate-600" />
              ) : (
                <ImageIcon className="h-6 w-6 text-slate-600" />
              )}
              <h3 className="font-semibold text-slate-900">
                {mode === 'video' ? 'Original Video' : 'Reference Photo'}
              </h3>
            </div>
            <div className="space-y-2 text-sm text-slate-600">
              <div>
                <span className="font-medium">File:</span> {files.reference.name}
              </div>
              <div>
                <span className="font-medium">Size:</span> {formatBytes(files.reference.size)}
              </div>
              <div>
                <span className="font-medium">Type:</span> {files.reference.type}
              </div>
            </div>
          </div>
        )}

        {files.target && (
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-3 mb-3">
              <FileVideo className="h-6 w-6 text-slate-600" />
              <h3 className="font-semibold text-slate-900">
                Suspected Deepfake Video
              </h3>
            </div>
            <div className="space-y-2 text-sm text-slate-600">
              <div>
                <span className="font-medium">File:</span> {files.target.name}
              </div>
              <div>
                <span className="font-medium">Size:</span> {formatBytes(files.target.size)}
              </div>
              <div>
                <span className="font-medium">Type:</span> {files.target.type}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Processing Steps */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-6">Processing Pipeline</h3>
        
        <div className="space-y-4">
          {processingSteps.map((step, index) => {
            const isCompleted = index < currentStep
            const isActive = index === currentStep
            const isPending = index > currentStep

            return (
              <div key={step.id} className="flex items-center gap-4">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-full
                  ${isCompleted ? 'bg-green-500 text-white' : 
                    isActive ? 'bg-cyan-500 text-white' : 
                    'bg-slate-200 text-slate-500'}
                `}>
                  {isCompleted ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : isActive ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    step.icon
                  )}
                </div>
                
                <div className="flex-1">
                  <div className={`
                    font-medium
                    ${isCompleted ? 'text-green-700' :
                      isActive ? 'text-cyan-700' :
                      'text-slate-500'}
                  `}>
                    {step.label}
                  </div>
                  <div className={`
                    text-sm
                    ${isCompleted ? 'text-green-600' :
                      isActive ? 'text-cyan-600' :
                      'text-slate-400'}
                  `}>
                    {step.description}
                  </div>
                </div>

                <div className={`
                  text-sm font-medium
                  ${isCompleted ? 'text-green-600' :
                    isActive ? 'text-cyan-600' :
                    'text-slate-400'}
                `}>
                  {isCompleted ? 'Complete' :
                   isActive ? 'Processing...' :
                   'Pending'}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Analysis ID */}
      <div className="mt-6 text-center">
        <div className="text-sm text-slate-500">
          Analysis ID: <span className="font-mono text-slate-700">{analysisId}</span>
        </div>
      </div>
    </div>
  )
}