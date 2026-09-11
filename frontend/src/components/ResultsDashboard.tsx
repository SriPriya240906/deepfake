'use client'

import { useState, useEffect } from 'react'
import { 
  CheckCircle2, 
  AlertTriangle, 
  Shield, 
  BarChart3, 
  Clock, 
  Eye, 
  Download, 
  RefreshCw,
  ChevronRight,
  PlayCircle,
  Users,
  Zap,
  Wifi,
  WifiOff
} from 'lucide-react'
import { mockAnalysisResult, mockPhotoAnalysisResult, AnalysisResult } from '@/lib/mock-data'
import { apiClient, checkBackendConnection } from '@/lib/api'
import TimelineChart from './TimelineChart'
import FaceAnalysis from './FaceAnalysis'
import EvidencePanel from './EvidencePanel'

interface ResultsDashboardProps {
  mode: 'video' | 'photo'
  analysisId: string
  onNewAnalysis: () => void
}

type TabType = 'overview' | 'timeline' | 'analysis' | 'evidence'

export default function ResultsDashboard({ mode, analysisId, onNewAnalysis }: ResultsDashboardProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [results, setResults] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [isBackendConnected, setIsBackendConnected] = useState(false)
  
  useEffect(() => {
    loadResults()
  }, [analysisId])

  const loadResults = async () => {
    setLoading(true)
    
    // Check if backend is available
    const backendConnected = await checkBackendConnection()
    setIsBackendConnected(backendConnected)
    
    if (backendConnected) {
      try {
        const response = await apiClient.getAnalysisResults(analysisId)
        
        if (response.data && response.data.results) {
          // Convert API response to frontend format
          const apiResults = response.data
          const convertedResults: AnalysisResult = {
            id: apiResults.id,
            status: 'completed',
            type: mode,
            createdAt: apiResults.created_at,
            completedAt: apiResults.completed_at,
            progress: 100,
            referenceFile: apiResults.reference_file,
            targetFile: apiResults.target_file,
            results: {
              deepfakeScore: apiResults.results.deepfake_score,
              totalFrames: apiResults.results.total_frames,
              glitchFrames: apiResults.results.glitch_frames,
              manipulatedRegions: apiResults.results.manipulated_regions.map((r: any) => ({
                region: r.region,
                confidence: r.confidence,
                frameIndex: r.frame_index
              })),
              timeline: apiResults.results.timeline.map((t: any) => ({
                frameIndex: t.frame_index,
                timestamp: t.timestamp,
                isManipulated: t.is_manipulated,
                confidence: t.confidence
              })),
              evidence: apiResults.results.evidence.map((e: any) => ({
                type: e.type,
                frameIndex: e.frame_index,
                region: e.region,
                confidence: e.confidence,
                description: e.description
              }))
            }
          }
          
          setResults(convertedResults)
        } else {
          // Fallback to mock data if no results yet
          setResults(mode === 'video' ? mockAnalysisResult : mockPhotoAnalysisResult)
        }
      } catch (error) {
        console.error('Failed to load results:', error)
        // Fallback to mock data
        setResults(mode === 'video' ? mockAnalysisResult : mockPhotoAnalysisResult)
      }
    } else {
      // Use mock data when backend is not available
      setResults(mode === 'video' ? mockAnalysisResult : mockPhotoAnalysisResult)
    }
    
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
        <p className="text-slate-600">Loading analysis results...</p>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-slate-600">Failed to load analysis results</p>
        <button 
          onClick={onNewAnalysis}
          className="mt-4 bg-cyan-500 hover:bg-cyan-600 text-white px-6 py-2 rounded-lg transition-colors"
        >
          Start New Analysis
        </button>
      </div>
    )
  }

  const score = results.results?.deepfakeScore || 0
  const scoreColor = score >= 0.7 ? 'red' : score >= 0.4 ? 'yellow' : 'green'
  const riskLevel = score >= 0.7 ? 'High Risk' : score >= 0.4 ? 'Medium Risk' : 'Low Risk'

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'timeline', label: 'Timeline', icon: <Clock className="h-4 w-4" /> },
    { id: 'analysis', label: 'Face Analysis', icon: <Eye className="h-4 w-4" /> },
    { id: 'evidence', label: 'Evidence', icon: <Shield className="h-4 w-4" /> }
  ]

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className={`
          flex items-center justify-center w-20 h-20 mx-auto mb-6 rounded-full
          ${scoreColor === 'red' ? 'bg-red-100' : 
            scoreColor === 'yellow' ? 'bg-yellow-100' : 'bg-green-100'}
        `}>
          {scoreColor === 'red' ? (
            <AlertTriangle className="h-10 w-10 text-red-600" />
          ) : scoreColor === 'yellow' ? (
            <AlertTriangle className="h-10 w-10 text-yellow-600" />
          ) : (
            <CheckCircle2 className="h-10 w-10 text-green-600" />
          )}
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Analysis Complete
        </h1>
        <p className="text-xl text-slate-600 mb-2">
          {mode === 'video' 
            ? 'Video-to-video comparison analysis completed'
            : 'Photo-to-video verification analysis completed'
          }
        </p>
        
        {/* Backend Connection Status */}
        <div className="flex items-center justify-center gap-2 text-sm">
          {isBackendConnected ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-green-600">Connected to backend API</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-orange-500" />
              <span className="text-orange-600">Using mock data (backend offline)</span>
            </>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center justify-center gap-4 mb-8">
        <button
          onClick={onNewAnalysis}
          className="inline-flex items-center gap-2 bg-cyan-500 hover:bg-cyan-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          <RefreshCw className="h-5 w-5" />
          New Analysis
        </button>
        <button className="inline-flex items-center gap-2 bg-slate-200 hover:bg-slate-300 text-slate-700 px-6 py-3 rounded-lg font-medium transition-colors">
          <Download className="h-5 w-5" />
          Download Report
        </button>
      </div>

      {/* Main Results Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-8 mb-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Deepfake Score */}
          <div className="text-center">
            <div className="text-6xl font-bold mb-2" style={{
              color: scoreColor === 'red' ? '#dc2626' : 
                     scoreColor === 'yellow' ? '#d97706' : '#059669'
            }}>
              {Math.round(score * 100)}%
            </div>
            <div className="text-lg font-semibold text-slate-900 mb-1">
              Deepfake Score
            </div>
            <div className={`
              text-sm font-medium px-3 py-1 rounded-full inline-block
              ${scoreColor === 'red' ? 'bg-red-100 text-red-800' :
                scoreColor === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'}
            `}>
              {riskLevel}
            </div>
          </div>

          {/* Statistics */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Total Frames</span>
              <span className="font-semibold text-slate-900">{results.results?.totalFrames}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Glitch Frames</span>
              <span className="font-semibold text-slate-900">{results.results?.glitchFrames}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Manipulated Regions</span>
              <span className="font-semibold text-slate-900">{results.results?.manipulatedRegions.length}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Evidence Items</span>
              <span className="font-semibold text-slate-900">{results.results?.evidence.length}</span>
            </div>
          </div>

          {/* Key Findings */}
          <div className="space-y-3">
            <h4 className="font-semibold text-slate-900 mb-3">Key Findings</h4>
            {results.results?.manipulatedRegions.slice(0, 3).map((region, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-2 h-2 bg-red-500 rounded-full flex-shrink-0"></div>
                <div className="text-sm">
                  <span className="font-medium text-slate-900">{region.region}</span>
                  <span className="text-slate-600"> - {Math.round(region.confidence * 100)}% confidence</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl border border-slate-200 mb-8">
        <div className="flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`
                flex items-center gap-2 px-6 py-4 font-medium transition-colors whitespace-nowrap
                ${activeTab === tab.id
                  ? 'bg-cyan-50 text-cyan-600 border-b-2 border-cyan-500'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }
              `}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="space-y-8">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Analysis Summary */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Analysis Summary</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <PlayCircle className="h-5 w-5 text-cyan-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-medium text-slate-900">
                      {mode === 'video' ? 'Frame-by-frame Comparison' : 'Identity Verification'}
                    </div>
                    <div className="text-sm text-slate-600">
                      {mode === 'video' 
                        ? 'Analyzed temporal consistency between original and target videos'
                        : 'Verified person identity against reference photo'
                      }
                    </div>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Eye className="h-5 w-5 text-cyan-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-medium text-slate-900">Facial Landmark Analysis</div>
                    <div className="text-sm text-slate-600">
                      Tracked 468 facial landmarks across all frames for displacement detection
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Zap className="h-5 w-5 text-cyan-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-medium text-slate-900">Artifact Detection</div>
                    <div className="text-sm text-slate-600">
                      Used SSIM and pixel difference analysis to identify manipulation artifacts
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Risk Assessment */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Risk Assessment</h3>
              <div className="space-y-4">
                <div className={`
                  p-4 rounded-lg border-l-4
                  ${scoreColor === 'red' ? 'bg-red-50 border-red-500' :
                    scoreColor === 'yellow' ? 'bg-yellow-50 border-yellow-500' :
                    'bg-green-50 border-green-500'}
                `}>
                  <div className={`
                    font-semibold mb-2
                    ${scoreColor === 'red' ? 'text-red-800' :
                      scoreColor === 'yellow' ? 'text-yellow-800' :
                      'text-green-800'}
                  `}>
                    {riskLevel}
                  </div>
                  <div className={`
                    text-sm
                    ${scoreColor === 'red' ? 'text-red-700' :
                      scoreColor === 'yellow' ? 'text-yellow-700' :
                      'text-green-700'}
                  `}>
                    {scoreColor === 'red' 
                      ? 'Strong indicators of deepfake manipulation detected. Multiple regions show significant inconsistencies.'
                      : scoreColor === 'yellow'
                      ? 'Some suspicious patterns detected. Further investigation recommended.'
                      : 'No significant manipulation artifacts detected. Video appears authentic.'
                    }
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">Confidence Level</span>
                    <span className="font-medium text-slate-900">
                      {Math.round((1 - Math.abs(score - 0.5) * 2) * 100)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">False Positive Risk</span>
                    <span className="font-medium text-slate-900">
                      {score < 0.3 ? 'Low' : score < 0.7 ? 'Medium' : 'High'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'timeline' && <TimelineChart results={results} />}
        {activeTab === 'analysis' && <FaceAnalysis results={results} mode={mode} />}
        {activeTab === 'evidence' && <EvidencePanel results={results} />}
      </div>
    </div>
  )
}