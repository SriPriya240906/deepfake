'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { 
  Upload, 
  FileVideo, 
  Image as ImageIcon, 
  X, 
  CheckCircle2, 
  AlertTriangle,
  Play
} from 'lucide-react'
import { cn, formatBytes } from '@/lib/utils'

interface FileUploadProps {
  mode: 'video' | 'photo'
  files: {
    reference?: File
    target?: File
  }
  onFilesReady: (files: { reference?: File; target?: File }) => void
  onStartAnalysis: () => void
}

export default function FileUpload({ mode, files, onFilesReady, onStartAnalysis }: FileUploadProps) {
  const [draggedOver, setDraggedOver] = useState<'reference' | 'target' | null>(null)

  const handleFileDrop = useCallback((acceptedFiles: File[], type: 'reference' | 'target') => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      const newFiles = { ...files, [type]: file }
      onFilesReady(newFiles)
    }
  }, [files, onFilesReady])

  const removeFile = (type: 'reference' | 'target') => {
    const newFiles = { ...files }
    delete newFiles[type]
    onFilesReady(newFiles)
  }

  const referenceDropzone = useDropzone({
    onDrop: (files) => handleFileDrop(files, 'reference'),
    accept: mode === 'video' ? { 'video/*': ['.mp4', '.avi', '.mov'] } : { 'image/*': ['.jpg', '.jpeg', '.png'] },
    maxFiles: 1,
    onDragEnter: () => setDraggedOver('reference'),
    onDragLeave: () => setDraggedOver(null),
    onDropAccepted: () => setDraggedOver(null),
    onDropRejected: () => setDraggedOver(null)
  })

  const targetDropzone = useDropzone({
    onDrop: (files) => handleFileDrop(files, 'target'),
    accept: { 'video/*': ['.mp4', '.avi', '.mov'] },
    maxFiles: 1,
    onDragEnter: () => setDraggedOver('target'),
    onDragLeave: () => setDraggedOver(null),
    onDropAccepted: () => setDraggedOver(null),
    onDropRejected: () => setDraggedOver(null)
  })

  const canStartAnalysis = files.reference && files.target

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          {mode === 'video' ? 'Upload Video Files' : 'Upload Photo and Video'}
        </h1>
        <p className="text-xl text-slate-600">
          {mode === 'video' 
            ? 'Upload the original video and the suspected deepfake for comparison'
            : 'Upload a reference photo and the suspected deepfake video'
          }
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        {/* Reference File Upload */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            {mode === 'video' ? (
              <FileVideo className="h-5 w-5 text-slate-600" />
            ) : (
              <ImageIcon className="h-5 w-5 text-slate-600" />
            )}
            <h3 className="text-lg font-semibold text-slate-900">
              {mode === 'video' ? 'Original Video' : 'Reference Photo'}
            </h3>
            <span className="text-sm text-red-500">*Required</span>
          </div>

          <div
            {...referenceDropzone.getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300",
              draggedOver === 'reference' ? "border-cyan-500 bg-cyan-50" :
              files.reference ? "border-green-500 bg-green-50" :
              "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
            )}
          >
            <input {...referenceDropzone.getInputProps()} />
            
            {files.reference ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center w-16 h-16 mx-auto bg-green-100 rounded-full">
                  <CheckCircle2 className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">{files.reference.name}</p>
                  <p className="text-sm text-slate-600">{formatBytes(files.reference.size)}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFile('reference')
                  }}
                  className="inline-flex items-center gap-2 text-red-600 hover:text-red-700 text-sm"
                >
                  <X className="h-4 w-4" />
                  Remove file
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center w-16 h-16 mx-auto bg-slate-100 rounded-full">
                  <Upload className="h-8 w-8 text-slate-600" />
                </div>
                <div>
                  <p className="text-lg font-medium text-slate-900">
                    Drop your {mode === 'video' ? 'original video' : 'reference photo'} here
                  </p>
                  <p className="text-slate-600">
                    or click to browse files
                  </p>
                  <p className="text-sm text-slate-500 mt-2">
                    {mode === 'video' 
                      ? 'Supports: MP4, AVI, MOV (max 100MB)'
                      : 'Supports: JPG, PNG (max 10MB)'
                    }
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Target Video Upload */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <FileVideo className="h-5 w-5 text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-900">
              Suspected Deepfake Video
            </h3>
            <span className="text-sm text-red-500">*Required</span>
          </div>

          <div
            {...targetDropzone.getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300",
              draggedOver === 'target' ? "border-cyan-500 bg-cyan-50" :
              files.target ? "border-green-500 bg-green-50" :
              "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
            )}
          >
            <input {...targetDropzone.getInputProps()} />
            
            {files.target ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center w-16 h-16 mx-auto bg-green-100 rounded-full">
                  <CheckCircle2 className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">{files.target.name}</p>
                  <p className="text-sm text-slate-600">{formatBytes(files.target.size)}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFile('target')
                  }}
                  className="inline-flex items-center gap-2 text-red-600 hover:text-red-700 text-sm"
                >
                  <X className="h-4 w-4" />
                  Remove file
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center w-16 h-16 mx-auto bg-slate-100 rounded-full">
                  <Upload className="h-8 w-8 text-slate-600" />
                </div>
                <div>
                  <p className="text-lg font-medium text-slate-900">
                    Drop your suspected deepfake video here
                  </p>
                  <p className="text-slate-600">
                    or click to browse files
                  </p>
                  <p className="text-sm text-slate-500 mt-2">
                    Supports: MP4, AVI, MOV (max 100MB)
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Analysis Settings */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Analysis Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Landmark Jump Threshold
            </label>
            <input
              type="range"
              min="1"
              max="50"
              defaultValue="10"
              className="w-full"
            />
            <div className="text-sm text-slate-500 mt-1">10.0 pixels</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Pixel Difference Threshold
            </label>
            <input
              type="range"
              min="5"
              max="60"
              defaultValue="20"
              className="w-full"
            />
            <div className="text-sm text-slate-500 mt-1">20</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              SSIM Threshold
            </label>
            <input
              type="range"
              min="50"
              max="100"
              defaultValue="85"
              className="w-full"
            />
            <div className="text-sm text-slate-500 mt-1">0.85</div>
          </div>
        </div>
      </div>

      {/* File Validation Messages */}
      {!canStartAnalysis && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
            <div>
              <p className="font-medium text-amber-800">
                Please upload both required files to continue
              </p>
              <p className="text-amber-700 text-sm mt-1">
                {!files.reference && `• ${mode === 'video' ? 'Original video' : 'Reference photo'} is required`}
                {!files.target && `• Suspected deepfake video is required`}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Start Analysis Button */}
      <div className="text-center">
        <button
          onClick={onStartAnalysis}
          disabled={!canStartAnalysis}
          className={cn(
            "inline-flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300",
            canStartAnalysis
              ? "bg-cyan-500 hover:bg-cyan-600 text-white shadow-lg hover:shadow-xl hover:scale-105"
              : "bg-slate-200 text-slate-500 cursor-not-allowed"
          )}
        >
          <Play className="h-6 w-6" />
          Start Forensic Analysis
        </button>
        
        {canStartAnalysis && (
          <p className="text-sm text-slate-600 mt-3">
            Estimated analysis time: 2-5 minutes
          </p>
        )}
      </div>
    </div>
  )
}