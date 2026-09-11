'use client'

import { useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { 
  ArrowLeft, 
  Shield, 
  Play, 
  Eye, 
  Upload, 
  FileVideo, 
  Image as ImageIcon, 
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiClient, checkBackendConnection } from '@/lib/api'
import FileUpload from '@/components/FileUpload'
import ProcessingState from '@/components/ProcessingState'
import ResultsDashboard from '@/components/ResultsDashboard'

type AnalysisMode = 'video' | 'photo'
type AnalysisStep = 'setup' | 'upload' | 'processing' | 'results'

export default function AnalyzePage() {
  const searchParams = useSearchParams()
  const initialMode = (searchParams.get('mode') as AnalysisMode) || 'video'
  
  const [mode, setMode] = useState<AnalysisMode>(initialMode)
  const [step, setStep] = useState<AnalysisStep>('setup')
  const [files, setFiles] = useState<{
    reference?: File
    target?: File
  }>({})
  const [analysisId, setAnalysisId] = useState<string>('')

  const handleModeSelect = (selectedMode: AnalysisMode) => {
    setMode(selectedMode)
    setStep('upload')
    setFiles({}) // Reset files when switching modes
  }

  const handleFilesReady = (uploadedFiles: { reference?: File; target?: File }) => {
    setFiles(uploadedFiles)
  }

  const handleStartAnalysis = async () => {
    if (!files.reference || !files.target) return
    
    setStep('processing')
    
    try {
      // Make actual API call based on mode
      const response = mode === 'video' 
        ? await apiClient.startVideoAnalysis(files.reference, files.target)
        : await apiClient.startPhotoAnalysis(files.reference, files.target)
      
      if (response.error) {
        console.error('Analysis failed to start:', response.error)
        // For demo purposes, fall back to mock mode
        const mockAnalysisId = `analysis_${Date.now()}`
        setAnalysisId(mockAnalysisId)
        
        // Simulate processing time
        setTimeout(() => {
          setStep('results')
        }, 3000)
      } else if (response.data) {
        setAnalysisId(response.data.analysis_id)
        
        // Start polling for status updates
        pollAnalysisStatus(response.data.analysis_id)
      }
    } catch (error) {
      console.error('Failed to start analysis:', error)
      
      // Fallback to mock analysis for demo
      const mockAnalysisId = `analysis_${Date.now()}`
      setAnalysisId(mockAnalysisId)
      
      setTimeout(() => {
        setStep('results')
      }, 3000)
    }
  }

  const pollAnalysisStatus = async (analysisId: string) => {
    const maxAttempts = 60 // 5 minutes with 5-second intervals
    let attempts = 0
    
    const poll = async () => {
      try {
        const response = await apiClient.getAnalysisStatus(analysisId)
        
        if (response.error || !response.data) {
          // If polling fails, continue with mock behavior
          setTimeout(() => {
            setStep('results')
          }, 2000)
          return
        }
        
        const status = response.data
        
        // Log the status for debugging
        console.log('Analysis status:', status)
        
        if (status.status === 'completed') {
          setStep('results')
        } else if (status.status === 'failed') {
          console.error('Analysis failed:', status.error_message)
          setStep('results') // Show results page with error state
        } else if (attempts < maxAttempts) {
          // Continue polling
          attempts++
          setTimeout(poll, 5000) // Poll every 5 seconds
        } else {
          // Timeout - show results anyway
          setStep('results')
        }
      } catch (error) {
        console.error('Status polling error:', error)
        // Fallback to showing results
        setTimeout(() => {
          setStep('results')
        }, 1000)
      }
    }
    
    // Start polling after a short delay
    setTimeout(poll, 2000)
  }

  const handleNewAnalysis = () => {
    setStep('setup')
    setFiles({})
    setAnalysisId('')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link 
                href="/" 
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
              >
                <ArrowLeft className="h-5 w-5" />
                Back to Home
              </Link>
              <div className="h-6 w-px bg-slate-300" />
              <div className="flex items-center gap-2">
                <Shield className="h-6 w-6 text-cyan-500" />
                <span className="text-xl font-bold text-slate-900">ForensicAI</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-sm text-slate-500">
                Analysis Mode: <span className="font-medium text-slate-700">{mode === 'video' ? 'Video-to-Video' : 'Photo-to-Video'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {['setup', 'upload', 'processing', 'results'].map((currentStep, index) => {
              const isActive = step === currentStep
              const isCompleted = ['setup', 'upload', 'processing', 'results'].indexOf(step) > index
              
              return (
                <div key={currentStep} className="flex items-center">
                  <div className={cn(
                    "flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium",
                    isActive ? "bg-cyan-500 text-white" :
                    isCompleted ? "bg-green-500 text-white" :
                    "bg-slate-200 text-slate-600"
                  )}>
                    {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : index + 1}
                  </div>
                  <span className={cn(
                    "ml-2 text-sm font-medium capitalize",
                    isActive ? "text-cyan-600" :
                    isCompleted ? "text-green-600" :
                    "text-slate-500"
                  )}>
                    {currentStep}
                  </span>
                  {index < 3 && (
                    <div className={cn(
                      "w-16 h-0.5 mx-4",
                      isCompleted ? "bg-green-500" : "bg-slate-200"
                    )} />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {step === 'setup' && (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-slate-900 mb-4">Choose Analysis Method</h1>
              <p className="text-xl text-slate-600">
                Select the type of forensic analysis you want to perform
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Video-to-Video Analysis */}
              <div 
                className={cn(
                  "bg-white p-8 rounded-xl border-2 cursor-pointer transition-all duration-300 hover:shadow-lg",
                  mode === 'video' ? "border-cyan-500 shadow-lg" : "border-slate-200 hover:border-slate-300"
                )}
                onClick={() => handleModeSelect('video')}
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="bg-cyan-500/10 p-4 rounded-xl">
                    <Play className="h-8 w-8 text-cyan-500" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-semibold text-slate-900">Video-to-Video Analysis</h3>
                    <p className="text-slate-600">Compare original vs suspected deepfake videos</p>
                  </div>
                </div>
                
                <div className="space-y-3 mb-6">
                  <div className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span>Frame-by-frame comparison analysis</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span>Temporal inconsistency detection</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span>Artifact region identification</span>
                  </div>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-slate-700 mb-2">Required Files:</div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <FileVideo className="h-4 w-4" />
                    <span>Original (reference) video</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600 mt-1">
                    <FileVideo className="h-4 w-4" />
                    <span>Suspected deepfake video</span>
                  </div>
                </div>
              </div>

              {/* Photo-to-Video Analysis */}
              <div 
                className={cn(
                  "bg-white p-8 rounded-xl border-2 cursor-pointer transition-all duration-300 hover:shadow-lg",
                  mode === 'photo' ? "border-cyan-500 shadow-lg" : "border-slate-200 hover:border-slate-300"
                )}
                onClick={() => handleModeSelect('photo')}
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="bg-cyan-500/10 p-4 rounded-xl">
                    <Eye className="h-8 w-8 text-cyan-500" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-semibold text-slate-900">Photo-to-Video Verification</h3>
                    <p className="text-slate-600">Verify person identity in suspected deepfake</p>
                  </div>
                </div>
                
                <div className="space-y-3 mb-6">
                  <div className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span>Identity verification analysis</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span>Facial geometry consistency check</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span>Manipulation probability scoring</span>
                  </div>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-slate-700 mb-2">Required Files:</div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <ImageIcon className="h-4 w-4" />
                    <span>Reference photo of person</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600 mt-1">
                    <FileVideo className="h-4 w-4" />
                    <span>Suspected deepfake video</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'upload' && (
          <FileUpload
            mode={mode}
            onFilesReady={handleFilesReady}
            onStartAnalysis={handleStartAnalysis}
            files={files}
          />
        )}

        {step === 'processing' && (
          <ProcessingState
            mode={mode}
            analysisId={analysisId}
            files={files}
          />
        )}

        {step === 'results' && (
          <ResultsDashboard
            mode={mode}
            analysisId={analysisId}
            onNewAnalysis={handleNewAnalysis}
          />
        )}
      </main>
    </div>
  )
}