export function Sidebar() {
  return (
    <div className="w-64 h-screen bg-gray-900 text-white p-4">
      <h1 className="text-xl font-bold mb-4">Live AI Assistant</h1>

      <button className="w-full bg-blue-600 hover:bg-blue-700 p-2 rounded">
        Start a new conversation
      </button>

      <div className="mt-6 text-sm text-gray-400">
        Conversations will appear here
      </div>
    </div>
  );
}