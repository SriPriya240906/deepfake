'use client'

import { useState } from 'react'
import { Play, Pause, SkipBack, SkipForward, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { AnalysisResult } from '@/lib/mock-data'
import { formatDuration } from '@/lib/utils'

interface TimelineChartProps {
  results: AnalysisResult
}

export default function TimelineChart({ results }: TimelineChartProps) {
  const [selectedFrame, setSelectedFrame] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  const timeline = results.results?.timeline || []
  const totalFrames = results.results?.totalFrames || 0
  const fps = 30 // Assuming 30 FPS

  const handleFrameClick = (frameIndex: number) => {
    setSelectedFrame(frameIndex)
    setIsPlaying(false)
  }

  const selectedFrameData = timeline[selectedFrame]

  return (
    <div className="space-y-6">
      {/* Timeline Visualization */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-900">Frame-by-Frame Timeline</h3>
          <div className="flex items-center gap-4 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span>Clean Frames</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span>Manipulated</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span>Suspicious</span>
            </div>
          </div>
        </div>

        {/* Timeline Chart */}
        <div className="bg-slate-50 rounded-lg p-4 mb-4">
          <div className="flex items-end h-32 gap-1 overflow-x-auto pb-2">
            {timeline.slice(0, 200).map((frame, index) => {
              const height = Math.max(frame.confidence * 100, 10) // Min 10px height
              const color = frame.isManipulated 
                ? frame.confidence > 0.8 ? 'bg-red-500' : 'bg-yellow-500'
                : 'bg-green-500'
              
              return (
                <div
                  key={index}
                  className={`
                    ${color} cursor-pointer transition-all hover:opacity-80 min-w-[2px] rounded-t
                    ${selectedFrame === index ? 'ring-2 ring-cyan-500 ring-offset-1' : ''}
                  `}
                  style={{ height: `${height}px` }}
                  onClick={() => handleFrameClick(index)}
                  title={`Frame ${index}: ${frame.isManipulated ? 'Manipulated' : 'Clean'} (${Math.round(frame.confidence * 100)}%)`}
                />
              )
            })}
          </div>
          
          {/* Timeline Scrubber */}
          <div className="relative mt-4">
            <div className="w-full h-2 bg-slate-200 rounded-full">
              <div 
                className="h-2 bg-cyan-500 rounded-full transition-all"
                style={{ width: `${(selectedFrame / (totalFrames - 1)) * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-2">
              <span>0:00</span>
              <span>{formatDuration(totalFrames / fps)}</span>
            </div>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-center gap-4">
          <button className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <SkipBack className="h-5 w-5 text-slate-600" />
          </button>
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors"
          >
            {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6" />}
          </button>
          <button className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <SkipForward className="h-5 w-5 text-slate-600" />
          </button>
        </div>
      </div>

      {/* Selected Frame Details */}
      {selectedFrameData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h4 className="text-lg font-semibold text-slate-900 mb-4">Frame Details</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Frame Index</span>
                <span className="font-medium text-slate-900">#{selectedFrame}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Timestamp</span>
                <span className="font-medium text-slate-900">
                  {formatDuration(selectedFrameData.timestamp)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Status</span>
                <div className="flex items-center gap-2">
                  {selectedFrameData.isManipulated ? (
                    <>
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <span className="text-red-600 font-medium">Manipulated</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span className="text-green-600 font-medium">Clean</span>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Confidence</span>
                <span className="font-medium text-slate-900">
                  {Math.round(selectedFrameData.confidence * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* Frame Preview Placeholder */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h4 className="text-lg font-semibold text-slate-900 mb-4">Frame Preview</h4>
            <div className="aspect-video bg-slate-100 rounded-lg flex items-center justify-center">
              <div className="text-center text-slate-500">
                <Play className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Frame preview will be available in next phase</p>
                <p className="text-xs text-slate-400 mt-1">Frame #{selectedFrame}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Statistics */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h4 className="text-lg font-semibold text-slate-900 mb-4">Timeline Statistics</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 mb-1">
              {timeline.filter(f => !f.isManipulated).length}
            </div>
            <div className="text-sm text-slate-600">Clean Frames</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600 mb-1">
              {timeline.filter(f => f.isManipulated).length}
            </div>
            <div className="text-sm text-slate-600">Manipulated Frames</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-cyan-600 mb-1">
              {Math.round((timeline.reduce((sum, f) => sum + f.confidence, 0) / timeline.length) * 100)}%
            </div>
            <div className="text-sm text-slate-600">Avg. Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 mb-1">
              {formatDuration(totalFrames / fps)}
            </div>
            <div className="text-sm text-slate-600">Total Duration</div>
          </div>
        </div>
      </div>
    </div>
  )
}