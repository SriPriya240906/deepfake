import Link from "next/link";
import { Shield, Eye, Zap, CheckCircle, ArrowRight, Play } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between p-6 lg:px-8">
        <div className="flex items-center gap-2">
          <Shield className="h-8 w-8 text-cyan-400" />
          <span className="text-2xl font-bold text-white">ForensicAI</span>
        </div>
        <div className="hidden md:flex items-center gap-6">
          <Link href="/analyze" className="text-slate-300 hover:text-white transition-colors">
            Analysis
          </Link>
          <Link href="/docs" className="text-slate-300 hover:text-white transition-colors">
            Documentation
          </Link>
          <Link 
            href="/analyze" 
            className="bg-cyan-500 hover:bg-cyan-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Start Analysis
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 pt-12 pb-24">
        <div className="text-center">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Professional
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400"> Deepfake</span>
            <br />
            Detection Suite
          </h1>
          <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            Advanced forensic analysis platform for video authenticity verification. 
            Detect manipulated content with military-grade precision using cutting-edge AI algorithms.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link 
              href="/analyze" 
              className="bg-cyan-500 hover:bg-cyan-600 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-300 hover:scale-105 flex items-center gap-2 justify-center"
            >
              <Play className="h-5 w-5" />
              Start Analysis
            </Link>
            <button className="border border-slate-500 text-slate-300 hover:text-white hover:border-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors flex items-center gap-2 justify-center">
              <Eye className="h-5 w-5" />
              View Demo
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
            <div className="text-center">
              <div className="text-4xl font-bold text-cyan-400 mb-2">99.7%</div>
              <div className="text-slate-300">Detection Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-cyan-400 mb-2">&lt;2min</div>
              <div className="text-slate-300">Average Analysis Time</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-cyan-400 mb-2">468</div>
              <div className="text-slate-300">Facial Landmarks Tracked</div>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
            <Shield className="h-12 w-12 text-cyan-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-3">Military-Grade Detection</h3>
            <p className="text-slate-400">
              Advanced algorithms analyze 468 facial landmarks, temporal inconsistencies, and pixel-level artifacts.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
            <Zap className="h-12 w-12 text-cyan-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-3">Real-Time Processing</h3>
            <p className="text-slate-400">
              Process videos up to 10GB with frame-by-frame analysis completing in under 2 minutes.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm p-6 rounded-xl border border-slate-700">
            <Eye className="h-12 w-12 text-cyan-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-3">Detailed Forensics</h3>
            <p className="text-slate-400">
              Comprehensive reports with timeline analysis, evidence mapping, and confidence scores.
            </p>
          </div>
        </div>

        {/* Analysis Types */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">Analysis Capabilities</h2>
          <p className="text-xl text-slate-300 mb-12">Choose the analysis method that fits your investigation</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-20">
          <Link href="/analyze?mode=video" className="group">
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-8 rounded-2xl border border-slate-700 hover:border-cyan-500 transition-all duration-300 hover:scale-105">
              <div className="flex items-center gap-4 mb-6">
                <div className="bg-cyan-500/20 p-3 rounded-xl">
                  <Play className="h-8 w-8 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-semibold text-white">Video-to-Video Analysis</h3>
                  <p className="text-slate-400">Compare original vs suspected deepfake videos</p>
                </div>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3 text-slate-300">
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                  Frame-by-frame comparison analysis
                </li>
                <li className="flex items-center gap-3 text-slate-300">
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                  Temporal inconsistency detection
                </li>
                <li className="flex items-center gap-3 text-slate-300">
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                  Artifact region identification
                </li>
              </ul>
              <div className="flex items-center gap-2 text-cyan-400 font-medium group-hover:gap-3 transition-all">
                Start Video Analysis <ArrowRight className="h-5 w-5" />
              </div>
            </div>
          </Link>

          <Link href="/analyze?mode=photo" className="group">
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-8 rounded-2xl border border-slate-700 hover:border-cyan-500 transition-all duration-300 hover:scale-105">
              <div className="flex items-center gap-4 mb-6">
                <div className="bg-cyan-500/20 p-3 rounded-xl">
                  <Eye className="h-8 w-8 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-semibold text-white">Photo-to-Video Verification</h3>
                  <p className="text-slate-400">Verify person identity in suspected deepfake</p>
                </div>
              </div>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-3 text-slate-300">
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                  Identity verification analysis
                </li>
                <li className="flex items-center gap-3 text-slate-300">
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                  Facial geometry consistency check
                </li>
                <li className="flex items-center gap-3 text-slate-300">
                  <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                  Manipulation probability scoring
                </li>
              </ul>
              <div className="flex items-center gap-2 text-cyan-400 font-medium group-hover:gap-3 transition-all">
                Start Photo Analysis <ArrowRight className="h-5 w-5" />
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse delay-1000"></div>
      </div>
    </div>
  );
}
