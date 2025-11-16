from flask import Flask, render_template, request, jsonify
from search_engine.searcher import SearchEngine
import os

app = Flask(__name__)
search_engine = SearchEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return render_template('index.html')
    
    results, total_results, search_time = search_engine.search(query, page=page)
    
    return render_template('results.html', 
                         query=query,
                         results=results,
                         total_results=total_results,
                         search_time=search_time,
                         current_page=page)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return jsonify({'error': 'No query provided'})
    
    results, total_results, search_time = search_engine.search(query, page=page)
    
    return jsonify({
        'query': query,
        'results': results,
        'total_results': total_results,
        'search_time': search_time,
        'current_page': page
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
