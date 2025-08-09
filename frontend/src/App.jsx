import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [ query, setQuery] = useState('');
  const [response, setReponse] = useState(null);
  const [loading,setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true)
    setReponse(null);
    setError(null);

    try{
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json();
      setReponse(data.response)
    }catch(e) {
      console.error("Failed to fetch:", e);
      setError("Failed to get a response from the server. Please ensure the backend is running.");
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className='min-h-screen bg-gray-50 flex flex-col items-center p-6'>
      <header className='text-center mb-8'>
        <h1 className='text-4xl font-bold text-gray-800 mb-2'>HR Chatbot</h1>
        <p className='text-gray-600'>Ask a question to find relevant employees</p>
      </header>

      <main className='w-full max-w-xl bg-white p-6 rounded-xl shadow-md'>
        <form onSubmit={handleSubmit}>
          <input 
            type='text'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'Find Python developers with 3+ years experience'"
            className='flex-1 border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 '
          />
          <button
            type='submit'
            disabled={loading}
            className='bg-blue-600 text-white font-medium px-6 py-2 mr-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50'
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </form>

        {response && (
          <div className='mt-6 bg-gray-100 p-4 rounded-lg overflow-auto'>
            <pre className="text-sm text-gray-800 whitespace-pre-wrap">
              {response}
            </pre>
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-100 text-red-700 rounded-lg">
            <p>{error}</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
