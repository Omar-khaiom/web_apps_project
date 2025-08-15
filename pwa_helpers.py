#!/usr/bin/env python3
"""
PWA Helpers for SmartRecipes
Enhanced caching and offline data management
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PWADataManager:
    """Manages PWA-related data and caching"""
    
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_pwa_tables()
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_pwa_tables(self):
        """Initialize PWA-specific database tables"""
        with self.get_db_connection() as conn:
            # Search history table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    search_term TEXT NOT NULL,
                    ingredients TEXT NOT NULL,
                    results_preview TEXT,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            ''')
            
            # Cached recipes table for offline access
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cached_recipes (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    image_url TEXT,
                    recipe_data TEXT NOT NULL,
                    cached_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # PWA installation tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pwa_installs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    user_agent TEXT,
                    install_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            ''')
        
        logger.info("PWA database tables initialized")
    
    def save_search_history(self, username, search_term, ingredients, results_preview=None):
        """Save search history for offline access"""
        try:
            with self.get_db_connection() as conn:
                # Convert results to JSON string if provided
                results_json = json.dumps(results_preview) if results_preview else None
                
                conn.execute('''
                    INSERT INTO search_history (username, search_term, ingredients, results_preview)
                    VALUES (?, ?, ?, ?)
                ''', (username, search_term, ','.join(ingredients), results_json))
                
                # Keep only last 50 searches per user
                conn.execute('''
                    DELETE FROM search_history 
                    WHERE username = ? AND id NOT IN (
                        SELECT id FROM search_history 
                        WHERE username = ? 
                        ORDER BY search_date DESC 
                        LIMIT 50
                    )
                ''', (username, username))
                
            logger.info(f"Search history saved for user {username}: {search_term}")
            return True
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            return False
    
    def get_search_history(self, username, limit=10):
        """Get recent search history for user"""
        try:
            with self.get_db_connection() as conn:
                results = conn.execute('''
                    SELECT search_term, ingredients, results_preview, search_date
                    FROM search_history
                    WHERE username = ?
                    ORDER BY search_date DESC
                    LIMIT ?
                ''', (username, limit)).fetchall()
                
                history = []
                for row in results:
                    history.append({
                        'search_term': row['search_term'],
                        'ingredients': row['ingredients'].split(',') if row['ingredients'] else [],
                        'results_preview': json.loads(row['results_preview']) if row['results_preview'] else None,
                        'search_date': row['search_date']
                    })
                
                return history
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            return []
    
    def cache_recipe(self, recipe_data):
        """Cache recipe data for offline access"""
        try:
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO cached_recipes (id, title, image_url, recipe_data, last_accessed)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    recipe_data['id'],
                    recipe_data['title'],
                    recipe_data.get('image', ''),
                    json.dumps(recipe_data),
                    datetime.now().isoformat()
                ))
                
                # Clean old cached recipes (keep last 100)
                conn.execute('''
                    DELETE FROM cached_recipes 
                    WHERE id NOT IN (
                        SELECT id FROM cached_recipes 
                        ORDER BY last_accessed DESC 
                        LIMIT 100
                    )
                ''')
                
            logger.info(f"Recipe cached: {recipe_data['title']}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache recipe: {e}")
            return False
    
    def get_cached_recipe(self, recipe_id):
        """Get cached recipe data"""
        try:
            with self.get_db_connection() as conn:
                # Update last accessed time
                conn.execute('''
                    UPDATE cached_recipes 
                    SET last_accessed = ? 
                    WHERE id = ?
                ''', (datetime.now().isoformat(), recipe_id))
                
                result = conn.execute('''
                    SELECT recipe_data FROM cached_recipes WHERE id = ?
                ''', (recipe_id,)).fetchone()
                
                if result:
                    return json.loads(result['recipe_data'])
                return None
        except Exception as e:
            logger.error(f"Failed to get cached recipe: {e}")
            return None
    
    def get_cached_recipes_list(self, limit=20):
        """Get list of cached recipes"""
        try:
            with self.get_db_connection() as conn:
                results = conn.execute('''
                    SELECT id, title, image_url, cached_date, last_accessed
                    FROM cached_recipes
                    ORDER BY last_accessed DESC
                    LIMIT ?
                ''', (limit,)).fetchall()
                
                cached_recipes = []
                for row in results:
                    cached_recipes.append({
                        'id': row['id'],
                        'title': row['title'],
                        'image_url': row['image_url'],
                        'cached_date': row['cached_date'],
                        'last_accessed': row['last_accessed']
                    })
                
                return cached_recipes
        except Exception as e:
            logger.error(f"Failed to get cached recipes list: {e}")
            return []
    
    def track_pwa_install(self, username, user_agent):
        """Track PWA installation"""
        try:
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO pwa_installs (username, user_agent)
                    VALUES (?, ?)
                ''', (username, user_agent))
                
            logger.info(f"PWA installation tracked for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to track PWA install: {e}")
            return False
    
    def get_pwa_stats(self):
        """Get PWA usage statistics"""
        try:
            with self.get_db_connection() as conn:
                # Total installs
                total_installs = conn.execute('SELECT COUNT(*) as count FROM pwa_installs').fetchone()['count']
                
                # Installs this month
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                monthly_installs = conn.execute('''
                    SELECT COUNT(*) as count FROM pwa_installs 
                    WHERE install_date > ?
                ''', (month_ago,)).fetchone()['count']
                
                # Cached recipes count
                cached_count = conn.execute('SELECT COUNT(*) as count FROM cached_recipes').fetchone()['count']
                
                # Search history count
                search_count = conn.execute('SELECT COUNT(*) as count FROM search_history').fetchone()['count']
                
                return {
                    'total_installs': total_installs,
                    'monthly_installs': monthly_installs,
                    'cached_recipes': cached_count,
                    'search_history_entries': search_count
                }
        except Exception as e:
            logger.error(f"Failed to get PWA stats: {e}")
            return {}
    
    def cleanup_old_data(self, days=30):
        """Clean up old cached data"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with self.get_db_connection() as conn:
                # Clean old search history
                deleted_searches = conn.execute('''
                    DELETE FROM search_history 
                    WHERE search_date < ?
                ''', (cutoff_date,)).rowcount
                
                # Clean old cached recipes (except recently accessed)
                deleted_recipes = conn.execute('''
                    DELETE FROM cached_recipes 
                    WHERE cached_date < ? AND last_accessed < ?
                ''', (cutoff_date, cutoff_date)).rowcount
                
            logger.info(f"Cleaned up {deleted_searches} old searches and {deleted_recipes} old cached recipes")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False

# Create global instance
pwa_manager = PWADataManager()

def enhance_search_with_history(username):
    """Get recent searches for autocomplete/suggestions"""
    if not username:
        return []
    
    history = pwa_manager.get_search_history(username, limit=5)
    suggestions = []
    
    for entry in history:
        suggestions.append({
            'search_term': entry['search_term'],
            'ingredients': entry['ingredients'],
            'date': entry['search_date']
        })
    
    return suggestions

def save_search_for_offline(username, search_term, ingredients, results):
    """Save search with preview results for offline access"""
    if not search_term or not ingredients:
        return False
    
    # Create preview from first 3 results
    results_preview = []
    if results:
        for recipe in results[:3]:
            results_preview.append({
                'id': recipe.get('id'),
                'title': recipe.get('title'),
                'image': recipe.get('image')
            })
    
    return pwa_manager.save_search_history(
        username or 'anonymous',
        search_term,
        ingredients,
        results_preview
    )

def cache_recipe_for_offline(recipe):
    """Cache recipe data for offline viewing"""
    if not recipe or not recipe.get('id'):
        return False
    
    return pwa_manager.cache_recipe(recipe)

def get_offline_content_stats(username):
    """Get offline content statistics for user"""
    stats = {
        'search_history_count': 0,
        'cached_recipes_count': 0,
        'recent_searches': []
    }
    
    if username:
        # Get recent searches count
        history = pwa_manager.get_search_history(username)
        stats['search_history_count'] = len(history)
        stats['recent_searches'] = history[:5]  # Last 5 searches
    
    # Get cached recipes count
    cached_recipes = pwa_manager.get_cached_recipes_list()
    stats['cached_recipes_count'] = len(cached_recipes)
    
    return stats
