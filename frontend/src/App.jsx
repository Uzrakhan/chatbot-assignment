import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import ReactMarkdown from 'react-markdown'

function App() {
  const [ query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading,setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true)
    setResponse(null);
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
      setResponse(data.response);

      // Clear input only if response is successful
      setQuery('');
    }catch(e) {
      console.error("Failed to fetch:", e);
      setError("Failed to get a response from the server. Please ensure the backend is running.");
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className='min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4 mb-6'>
      <div className='w-full max-w-3xl bg-white shadow-lg rounded-lg p-6'>
        <h1 className='text-3xl font-bold text-center text-gray-800 mb-2'>HR Chatbot</h1>
        <p className='text-center text-gray-600 mb-6'>Ask a question to find relevant employees</p>
      </div>

      <main className='w-full max-w-3xl bg-white p-6 rounded-xl shadow-md mt-5'>
        <form 
          onSubmit={(e) => {
            handleSubmit(e);
            e.target.reset(); // clears form fields
          }} 
          className='flex gap-2'>
          <input 
            type='text'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'Find Python developers with 3+ years experience'"
            className='flex-grow p-2  border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 '
          />
          <button
            type='submit'
            disabled={loading}
            className='px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-blue-300'
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </form>

        {response && (
          <div className='mt-6 bg-gray-50 p-4 border border-gray-200 rounded-md'>
            <p className='font-bold text-lg text-gray-800'>{response.intro}</p>
            <ul className='mt-4 space-y-4'>
              {response.candidates.map((employeeText, index) => (
                <li key={index} className='bg-white p-4 border border-gray-200 rounded-md shadow-sm'>
                  <ReactMarkdown  children={employeeText} />
                </li>
              ))}
            </ul>

            {/* Closing */}
            <p className='mt-6 text-gray-700'>{response.closing}</p>
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
            <p>{error}</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
