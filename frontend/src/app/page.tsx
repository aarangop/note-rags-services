export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Note RAGs
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Chat with your notes using AI
          </p>
        </header>

        <main className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
              Ask a Question
            </h2>

            {/* This is where we'll add the query form next */}
            <div className="space-y-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <p className="text-blue-800 dark:text-blue-200">
                  🚀 Frontend is ready! Query form coming next...
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
