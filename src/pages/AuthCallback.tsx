import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '@/utils/supabaseClient';
import { useApp } from '@/contexts/AppContext';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useApp();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing authentication...');
  const [debugInfo, setDebugInfo] = useState<any>({});

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // COMPREHENSIVE LOGGING - Step 1: Initial URL analysis
        const currentUrl = window.location.href;
        const currentOrigin = window.location.origin;
        const isProduction = currentOrigin.includes('lovable.app');
        
        console.log('🔄 AUTH CALLBACK DEBUG - Step 1: Starting auth callback processing...');
        console.log('🔍 CRITICAL - Environment Detection:');
        console.log('🔍 Current URL:', currentUrl);
        console.log('🔍 Current origin:', currentOrigin);
        console.log('🔍 Is production/staging:', isProduction);
        console.log('🔍 All URL params:', Object.fromEntries(searchParams.entries()));
        
        setDebugInfo(prev => ({
          ...prev,
          currentUrl,
          currentOrigin,
          isProduction,
          urlParams: Object.fromEntries(searchParams.entries())
        }));

        // COMPREHENSIVE LOGGING - Step 2: Supabase session handling
        console.log('🔄 AUTH CALLBACK DEBUG - Step 2: Getting Supabase session...');
        
        const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
        
        console.log('🔍 CRITICAL - Supabase Session Result:');
        console.log('🔍 Session data:', sessionData);
        console.log('🔍 Session error:', sessionError);
        console.log('🔍 User from session:', sessionData?.session?.user);
        
        if (sessionError) {
          console.error('❌ AUTH CALLBACK ERROR: Session error:', sessionError);
          setStatus('error');
          setMessage(`Session error: ${sessionError.message}`);
          setDebugInfo(prev => ({ ...prev, sessionError: sessionError.message }));
          
          // Still try to redirect after a delay to avoid infinite loops
          setTimeout(() => {
            console.log('🔄 Redirecting to login due to session error...');
            navigate('/login');
          }, 3000);
          return;
        }

        const session = sessionData?.session;
        if (!session || !session.user) {
          console.log('⚠️ AUTH CALLBACK: No session found, checking URL parameters...');
          
          // Check URL parameters for auth information
          const error = searchParams.get('error');
          const errorDescription = searchParams.get('error_description');
          
          if (error) {
            console.error('❌ AUTH CALLBACK ERROR: OAuth error from URL:', error, errorDescription);
            setStatus('error');
            setMessage(`Authentication failed: ${errorDescription || error}`);
            setTimeout(() => navigate('/login'), 2000);
            return;
          }
          
          console.error('❌ AUTH CALLBACK ERROR: No valid session or auth data');
          setStatus('error');
          setMessage('Authentication failed - no valid session found');
          setTimeout(() => navigate('/login'), 2000);
          return;
        }

        const finalUser = session?.user;
        
        console.log('✅ AUTH CALLBACK SUCCESS: Valid session found');
        console.log('🔍 Final user object:', finalUser);
        console.log('🔍 User email:', finalUser?.email);
        console.log('🔍 User metadata:', finalUser?.user_metadata);
        
        setStatus('success');
        setMessage('Authentication successful! Redirecting...');
        setDebugInfo(prev => ({
          ...prev,
          finalUser: {
            email: finalUser?.email,
            metadata: finalUser?.user_metadata,
            id: finalUser?.id
          }
        }));

        // COMPREHENSIVE LOGGING - Step 3: Database operations with fallback awareness
        console.log('🔄 AUTH CALLBACK DEBUG - Step 3: Processing user in context...');
        console.log('🔄 NOTE: If MongoDB CORS errors occur, app will use localStorage fallback');
        
        // Wait a moment for the session to be established
        setTimeout(() => {
          console.log('🔄 Redirecting to appropriate page...');
          
          // Check if user has completed onboarding
          if (user?.hasCompletedOnboarding) {
            console.log('🔄 User has completed onboarding, redirecting to dashboard');
            navigate('/dashboard');
          } else {
            console.log('🔄 User needs onboarding, redirecting to onboarding');
            navigate('/onboarding');
          }
        }, 1500);

      } catch (error: any) {
        console.error('❌ AUTH CALLBACK CRITICAL ERROR:', error);
        setStatus('error');
        setMessage(`Authentication error: ${error.message}`);
        setDebugInfo(prev => ({ ...prev, criticalError: error.message }));
        
        setTimeout(() => {
          console.log('🔄 Redirecting to login due to critical error...');
          navigate('/login');
        }, 3000);
      }
    };

    handleAuthCallback();
  }, [navigate, searchParams, user]);

  // Don't render anything if we already have a user and they've completed onboarding
  if (user?.hasCompletedOnboarding) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <div className="mb-6">
          {status === 'loading' && (
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          )}
          {status === 'success' && (
            <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          )}
          {status === 'error' && (
            <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          )}
        </div>
        
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {status === 'loading' && 'Processing Authentication...'}
          {status === 'success' && 'Authentication Successful!'}
          {status === 'error' && 'Authentication Error'}
        </h2>
        
        <p className="text-gray-600 mb-4">{message}</p>
        
        {status === 'success' && (
          <div className="text-sm text-gray-500">
            Setting up your account... This may take a moment.
          </div>
        )}
        
        {status === 'error' && (
          <div className="text-sm text-gray-500">
            You will be redirected to the login page shortly.
          </div>
        )}

        {/* Debug information for development */}
        {process.env.NODE_ENV === 'development' && Object.keys(debugInfo).length > 0 && (
          <details className="mt-4 text-left">
            <summary className="text-sm cursor-pointer text-gray-500">Debug Info</summary>
            <pre className="text-xs bg-gray-100 p-2 rounded mt-2 overflow-auto">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
};

export default AuthCallback; 