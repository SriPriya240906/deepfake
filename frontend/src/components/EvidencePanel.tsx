'use client'

import { useState } from 'react'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Eye, 
  Zap, 
  Download, 
  Filter,
  Search,
  ChevronRight
} from 'lucide-react'
import { AnalysisResult } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

interface EvidencePanelProps {
  results: AnalysisResult
}

type EvidenceType = 'all' | 'landmark_jump' | 'ssim_anomaly' | 'frame_difference'
type SeverityLevel = 'all' | 'high' | 'medium' | 'low'

export default function EvidencePanel({ results }: EvidencePanelProps) {
  const [filter, setFilter] = useState<EvidenceType>('all')
  const [severity, setSeverity] = useState<SeverityLevel>('all')
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null)
  
  const evidence = results.results?.evidence || []
  
  // Filter evidence based on selected filters
  const filteredEvidence = evidence.filter(item => {
    const typeMatch = filter === 'all' || item.type === filter
    const severityMatch = severity === 'all' || 
      (severity === 'high' && item.confidence > 0.8) ||
      (severity === 'medium' && item.confidence > 0.6 && item.confidence <= 0.8) ||
      (severity === 'low' && item.confidence <= 0.6)
    
    return typeMatch && severityMatch
  })

  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'landmark_jump':
        return <Eye className="h-5 w-5" />
      case 'ssim_anomaly':
        return <AlertTriangle className="h-5 w-5" />
      case 'frame_difference':
        return <Zap className="h-5 w-5" />
      default:
        return <Shield className="h-5 w-5" />
    }
  }

  const getEvidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'red'
    if (confidence > 0.6) return 'yellow'
    return 'orange'
  }

  const formatEvidenceType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  return (
    <div className="space-y-6">
      {/* Evidence Summary */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-6 w-6 text-cyan-500" />
          <h3 className="text-lg font-semibold text-slate-900">Forensic Evidence</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-1">
              {evidence.length}
            </div>
            <div className="text-sm text-slate-600">Total Evidence Items</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600 mb-1">
              {evidence.filter(e => e.confidence > 0.8).length}
            </div>
            <div className="text-sm text-slate-600">High Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600 mb-1">
              {evidence.filter(e => e.confidence > 0.6 && e.confidence <= 0.8).length}
            </div>
            <div className="text-sm text-slate-600">Medium Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-slate-900 mb-1">
              {new Set(evidence.map(e => e.region)).size}
            </div>
            <div className="text-sm text-slate-600">Affected Regions</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 p-4 bg-slate-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-600" />
            <span className="text-sm font-medium text-slate-700">Filters:</span>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Type:</span>
            <select 
              value={filter} 
              onChange={(e) => setFilter(e.target.value as EvidenceType)}
              className="text-sm border border-slate-300 rounded px-2 py-1"
            >
              <option value="all">All Types</option>
              <option value="landmark_jump">Landmark Jump</option>
              <option value="ssim_anomaly">SSIM Anomaly</option>
              <option value="frame_difference">Frame Difference</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Severity:</span>
            <select 
              value={severity} 
              onChange={(e) => setSeverity(e.target.value as SeverityLevel)}
              className="text-sm border border-slate-300 rounded px-2 py-1"
            >
              <option value="all">All Levels</option>
              <option value="high">High (80%+)</option>
              <option value="medium">Medium (60-80%)</option>
              <option value="low">Low (&lt;60%)</option>
            </select>
          </div>

          <div className="ml-auto">
            <button className="inline-flex items-center gap-2 text-sm bg-cyan-500 hover:bg-cyan-600 text-white px-3 py-1 rounded transition-colors">
              <Download className="h-4 w-4" />
              Export Evidence
            </button>
          </div>
        </div>
      </div>

      {/* Evidence List */}
      <div className="bg-white rounded-xl border border-slate-200">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-slate-900">
              Evidence Items ({filteredEvidence.length})
            </h4>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Search className="h-4 w-4" />
              <span>Click item for details</span>
            </div>
          </div>
        </div>

        <div className="divide-y divide-slate-200">
          {filteredEvidence.map((item, index) => {
            const color = getEvidenceColor(item.confidence)
            const isSelected = selectedEvidence === `${item.frameIndex}-${index}`
            
            return (
              <div key={`${item.frameIndex}-${index}`}>
                <div 
                  className={cn(
                    "p-4 cursor-pointer transition-colors hover:bg-slate-50",
                    isSelected && "bg-cyan-50 border-l-4 border-cyan-500"
                  )}
                  onClick={() => setSelectedEvidence(
                    isSelected ? null : `${item.frameIndex}-${index}`
                  )}
                >
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "flex items-center justify-center w-10 h-10 rounded-full",
                      color === 'red' ? 'bg-red-100 text-red-600' :
                      color === 'yellow' ? 'bg-yellow-100 text-yellow-600' :
                      'bg-orange-100 text-orange-600'
                    )}>
                      {getEvidenceIcon(item.type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <div className="font-medium text-slate-900">
                          {formatEvidenceType(item.type)}
                        </div>
                        <div className="text-sm text-slate-600">
                          Frame #{item.frameIndex}
                        </div>
                        <div className="text-sm font-medium text-slate-700">
                          {item.region}
                        </div>
                      </div>
                      <div className="text-sm text-slate-600 mt-1 truncate">
                        {item.description}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "px-3 py-1 rounded-full text-sm font-medium",
                        color === 'red' ? 'bg-red-100 text-red-800' :
                        color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-orange-100 text-orange-800'
                      )}>
                        {Math.round(item.confidence * 100)}%
                      </div>
                      
                      <ChevronRight className={cn(
                        "h-5 w-5 text-slate-400 transition-transform",
                        isSelected && "rotate-90"
                      )} />
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isSelected && (
                  <div className="px-4 pb-4 bg-slate-50 border-t border-slate-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                      <div>
                        <h5 className="font-medium text-slate-900 mb-3">Technical Details</h5>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-600">Detection Type:</span>
                            <span className="font-medium text-slate-900">
                              {formatEvidenceType(item.type)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Frame Index:</span>
                            <span className="font-medium text-slate-900">#{item.frameIndex}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Affected Region:</span>
                            <span className="font-medium text-slate-900">{item.region}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Confidence Score:</span>
                            <span className="font-medium text-slate-900">
                              {Math.round(item.confidence * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h5 className="font-medium text-slate-900 mb-3">Analysis</h5>
                        <div className="text-sm text-slate-700 leading-relaxed">
                          {item.description}
                        </div>
                        
                        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                          <div className="text-sm font-medium text-blue-800 mb-1">
                            Forensic Significance
                          </div>
                          <div className="text-sm text-blue-700">
                            {item.confidence > 0.8
                              ? 'Strong evidence of manipulation - suitable for forensic reporting'
                              : item.confidence > 0.6
                              ? 'Moderate evidence - requires additional validation'
                              : 'Weak evidence - potential false positive'
                            }
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}

          {filteredEvidence.length === 0 && (
            <div className="p-8 text-center text-slate-500">
              <Shield className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No evidence items match the current filters</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}