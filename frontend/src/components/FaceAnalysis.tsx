'use client'

import { useState } from 'react'
import { Eye, Target, AlertCircle, TrendingUp, Grid3X3 } from 'lucide-react'
import { AnalysisResult } from '@/lib/mock-data'

interface FaceAnalysisProps {
  results: AnalysisResult
  mode: 'video' | 'photo'
}

export default function FaceAnalysis({ results, mode }: FaceAnalysisProps) {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  
  const manipulatedRegions = results.results?.manipulatedRegions || []
  
  // Group regions by type for better visualization
  const regionGroups = manipulatedRegions.reduce((acc, region) => {
    const key = region.region
    if (!acc[key]) acc[key] = []
    acc[key].push(region)
    return acc
  }, {} as Record<string, typeof manipulatedRegions>)

  const faceRegions = [
    { id: 'LEFT EYE', label: 'Left Eye', x: 25, y: 30, color: 'bg-blue-500' },
    { id: 'RIGHT EYE', label: 'Right Eye', x: 65, y: 30, color: 'bg-blue-500' },
    { id: 'NOSE', label: 'Nose', x: 45, y: 50, color: 'bg-green-500' },
    { id: 'MOUTH', label: 'Mouth', x: 45, y: 70, color: 'bg-purple-500' },
    { id: 'LEFT CHEEK', label: 'Left Cheek', x: 20, y: 55, color: 'bg-yellow-500' },
    { id: 'RIGHT CHEEK', label: 'Right Cheek', x: 70, y: 55, color: 'bg-yellow-500' },
    { id: 'FOREHEAD', label: 'Forehead', x: 45, y: 20, color: 'bg-indigo-500' },
    { id: 'CHIN', label: 'Chin', x: 45, y: 85, color: 'bg-pink-500' },
    { id: 'JAW', label: 'Jaw', x: 45, y: 80, color: 'bg-orange-500' },
  ]

  return (
    <div className="space-y-6">
      {/* Analysis Overview */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Eye className="h-6 w-6 text-cyan-500" />
          <h3 className="text-lg font-semibold text-slate-900">Facial Region Analysis</h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Face Map */}
          <div>
            <h4 className="font-semibold text-slate-900 mb-4">Manipulation Heat Map</h4>
            <div className="relative">
              {/* Face Outline */}
              <div className="w-80 h-96 mx-auto relative bg-slate-100 rounded-full border-2 border-slate-200">
                <div className="absolute inset-4 bg-gradient-to-b from-slate-50 to-slate-100 rounded-full">
                  {/* Face regions */}
                  {faceRegions.map((region) => {
                    const isManipulated = regionGroups[region.id]
                    const confidence = isManipulated ? 
                      Math.max(...regionGroups[region.id].map(r => r.confidence)) : 0
                    
                    return (
                      <div
                        key={region.id}
                        className={`
                          absolute w-8 h-8 rounded-full cursor-pointer transition-all transform hover:scale-110
                          ${isManipulated 
                            ? confidence > 0.8 ? 'bg-red-500 ring-2 ring-red-300' :
                              confidence > 0.6 ? 'bg-orange-500 ring-2 ring-orange-300' :
                              'bg-yellow-500 ring-2 ring-yellow-300'
                            : 'bg-green-500 opacity-30'
                          }
                          ${selectedRegion === region.id ? 'ring-4 ring-cyan-500 ring-offset-2' : ''}
                        `}
                        style={{ 
                          left: `${region.x}%`, 
                          top: `${region.y}%`,
                          transform: 'translate(-50%, -50%)'
                        }}
                        onClick={() => setSelectedRegion(
                          selectedRegion === region.id ? null : region.id
                        )}
                        title={`${region.label}${isManipulated ? ` - ${Math.round(confidence * 100)}% confidence` : ' - Clean'}`}
                      >
                        {isManipulated && (
                          <AlertCircle className="h-4 w-4 text-white absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
              
              {/* Legend */}
              <div className="mt-4 flex justify-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span>Clean</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span>Low Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                  <span>Medium Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span>High Risk</span>
                </div>
              </div>
            </div>
          </div>

          {/* Region Details */}
          <div>
            <h4 className="font-semibold text-slate-900 mb-4">
              {selectedRegion ? `${selectedRegion} Analysis` : 'Select a region for details'}
            </h4>
            
            {selectedRegion && regionGroups[selectedRegion] ? (
              <div className="space-y-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium text-slate-900">{selectedRegion}</span>
                    <span className="text-sm text-red-600 font-medium">
                      {regionGroups[selectedRegion].length} detection(s)
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    {regionGroups[selectedRegion].map((detection, index) => (
                      <div key={index} className="flex items-center justify-between text-sm">
                        <span className="text-slate-600">Frame #{detection.frameIndex}</span>
                        <span className="font-medium text-slate-900">
                          {Math.round(detection.confidence * 100)}% confidence
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-medium text-amber-800 mb-1">Analysis Notes</div>
                      <div className="text-sm text-amber-700">
                        Multiple manipulation artifacts detected in this region. 
                        Inconsistencies suggest potential deepfake modification.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-lg p-8 text-center">
                <Target className="h-12 w-12 text-slate-400 mx-auto mb-3" />
                <p className="text-slate-600">
                  Click on a facial region in the map to view detailed analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Regional Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="h-5 w-5 text-cyan-500" />
            <h4 className="font-semibold text-slate-900">Most Affected Regions</h4>
          </div>
          
          <div className="space-y-3">
            {Object.entries(regionGroups)
              .sort(([,a], [,b]) => b.length - a.length)
              .slice(0, 5)
              .map(([region, detections]) => {
                const avgConfidence = detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length
                return (
                  <div key={region} className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-slate-900">{region}</div>
                      <div className="text-sm text-slate-600">
                        {detections.length} detection{detections.length !== 1 ? 's' : ''}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-slate-900">
                        {Math.round(avgConfidence * 100)}%
                      </div>
                      <div className="text-sm text-slate-600">avg. confidence</div>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Grid3X3 className="h-5 w-5 text-cyan-500" />
            <h4 className="font-semibold text-slate-900">Analysis Methodology</h4>
          </div>
          
          <div className="space-y-4 text-sm text-slate-600">
            <div>
              <div className="font-medium text-slate-900 mb-1">Landmark Tracking</div>
              <div>468 facial landmarks monitored for displacement anomalies</div>
            </div>
            
            <div>
              <div className="font-medium text-slate-900 mb-1">Temporal Analysis</div>
              <div>Frame-to-frame consistency validation using SSIM metrics</div>
            </div>
            
            <div>
              <div className="font-medium text-slate-900 mb-1">Pixel Analysis</div>
              <div>Intensity difference detection for artifact identification</div>
            </div>
            
            {mode === 'photo' && (
              <div>
                <div className="font-medium text-slate-900 mb-1">Identity Verification</div>
                <div>Reference photo comparison for person authentication</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}