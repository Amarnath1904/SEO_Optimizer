#!/usr/bin/env python3
"""
WordPress SEO Optimizer Script
This script connects to a WordPress site using Application Passwords for authentication
and optimizes published posts by adding/updating meta descriptions and keywords.
"""

import requests
import csv
import os
import json
import time
import google.generativeai as genai
from urllib.parse import urljoin
import html
import re


class WordPressSEOOptimizer:
    def __init__(self, base_url, username, app_password, gemini_api_key):
        """Initialize the WordPress SEO optimizer with API credentials"""
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.username = username
        self.app_password = app_password
        self.auth = (username, app_password)

        # Initialize Google Gemini API
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')

        # Set up logging and reporting
        self.report_data = []
        self.log_data = []

    def log(self, post_id, message):
        """Log messages for a specific post"""
        self.log_data.append({"post_id": post_id, "message": message})
        print(f"Post {post_id}: {message}")

    def get_all_published_posts(self):
        """Fetch all published posts from WordPress"""
        posts = []
        page = 1
        per_page = 100

        while True:
            response = requests.get(
                f"{self.api_url}/posts",
                params={
                    "status": "publish",
                    "per_page": per_page,
                    "page": page
                },
                auth=self.auth
            )

            if response.status_code != 200:
                print(f"Error fetching posts: {response.status_code} - {response.text}")
                break

            batch = response.json()
            if not batch:
                break

            posts.extend(batch)
            page += 1

            # Check if we've reached the last page
            if len(batch) < per_page:
                break

        print(f"Retrieved {len(posts)} published posts.")
        return posts

    def generate_meta_description(self, content, keyword=None, max_length=160):
        """Generate a meta description using Gemini API"""
        # Clean HTML content
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = html.unescape(clean_content)

        # Truncate content to avoid large API requests
        sample_content = clean_content[:1500]

        prompt = f"""
        Write a compelling meta description for a WordPress blog post.

        Content snippet: "{sample_content}"

        Requirements:
        - Maximum length: 160 characters
        - Include this keyword if provided: "{keyword if keyword else '[generate appropriate keyword]'}"
        - Focus on enticing readers to click
        - Be concise and informative
        - Use active voice
        - If no keyword is provided, include a relevant 2-3 word keyword phrase
        - Output ONLY the meta description text, nothing else

        If no keyword was provided, first identify a relevant 2-3 word keyword from the content, then include it naturally.
        """

        try:
            response = self.gemini_model.generate_content(prompt)
            meta_description = response.text.strip()

            # Ensure it doesn't exceed max length
            if len(meta_description) > max_length:
                meta_description = meta_description[:max_length - 3] + "..."

            return meta_description
        except Exception as e:
            print(f"Error generating meta description: {e}")
            return None

    def generate_keyword(self, content, title):
        """Generate a relevant keyword using Gemini API"""
        # Clean HTML content
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = html.unescape(clean_content)

        # Truncate content to avoid large API requests
        sample_content = clean_content[:1500]

        prompt = f"""
        Analyze this WordPress blog post and identify the most relevant 2-3 word SEO keyword phrase that:
        1. Accurately represents the main topic
        2. Has search value
        3. Is naturally usable in titles and descriptions

        Title: "{title}"
        Content snippet: "{sample_content}"

        Output ONLY the keyword phrase, nothing else.
        """

        try:
            response = self.gemini_model.generate_content(prompt)
            keyword = response.text.strip()

            # Clean up response to ensure we just get the keyword
            if ":" in keyword:
                keyword = keyword.split(":", 1)[1].strip()

            return keyword
        except Exception as e:
            print(f"Error generating keyword: {e}")
            return None

    def update_post_title(self, title, keyword):
        """Intelligently update post title to include keyword if not already present"""
        if keyword.lower() in title.lower():
            return title  # Keyword already in title

        # Try to naturally insert keyword
        try:
            prompt = f"""
            I need to include the keyword "{keyword}" in this title while maintaining readability:
            "{title}"

            Rules:
            - Make minimal changes to the original title
            - Keep the title natural and readable
            - If the keyword can't be naturally included, do not change the title
            - Output ONLY the updated title, nothing else
            """

            response = self.gemini_model.generate_content(prompt)
            new_title = response.text.strip()

            # Verify keyword was actually added
            if keyword.lower() not in new_title.lower():
                return title  # Return original if keyword wasn't added

            return new_title
        except Exception as e:
            print(f"Error updating title: {e}")
            return title

    def update_first_paragraph(self, content, keyword):
        """Update the first paragraph to include the keyword if not already present"""
        # Find the first paragraph
        match = re.search(r'<p>(.*?)</p>', content, re.DOTALL)
        if not match:
            return content  # No paragraph found

        first_para = match.group(1)
        first_para_clean = re.sub(r'<[^>]+>', '', first_para)

        # Check if keyword already exists in the first paragraph
        if keyword.lower() in first_para_clean.lower():
            return content

        try:
            # Get just the first paragraph to update
            prompt = f"""
            I need to include the keyword "{keyword}" in this paragraph while maintaining readability:
            "{first_para_clean}"

            Rules:
            - Make minimal changes to the original paragraph
            - Keep the text natural and readable
            - Output ONLY the updated paragraph, nothing else
            - Do not add any HTML tags
            """

            response = self.gemini_model.generate_content(prompt)
            new_para = response.text.strip()

            # Update the content
            updated_content = content.replace(first_para, new_para)
            return updated_content
        except Exception as e:
            print(f"Error updating first paragraph: {e}")
            return content

    def get_rank_math_data(self, post_id):
        """Get Rank Math SEO data for a post"""
        try:
            response = requests.get(
                f"{self.api_url}/posts/{post_id}",
                params={"context": "edit"},
                auth=self.auth
            )

            if response.status_code != 200:
                return None

            post_data = response.json()

            # Look for Rank Math data in meta
            rank_math_data = None
            if 'meta' in post_data and 'rank_math_data' in post_data['meta']:
                try:
                    if isinstance(post_data['meta']['rank_math_data'], str):
                        rank_math_data = json.loads(post_data['meta']['rank_math_data'])
                    else:
                        rank_math_data = post_data['meta']['rank_math_data']
                except:
                    rank_math_data = None

            return rank_math_data
        except Exception as e:
            print(f"Error fetching Rank Math data: {e}")
            return None

    def update_rank_math_keyword(self, post_id, keyword):
        """Update Rank Math keyword for a post"""
        try:
            # Get existing Rank Math data
            rank_math_data = self.get_rank_math_data(post_id)

            if rank_math_data is None:
                rank_math_data = {}

            # Update focus keyword
            rank_math_data['focus_keyword'] = keyword

            # Update post meta
            response = requests.post(
                f"{self.api_url}/posts/{post_id}",
                json={
                    "meta": {
                        "rank_math_data": json.dumps(rank_math_data)
                    }
                },
                auth=self.auth
            )

            return response.status_code == 200
        except Exception as e:
            print(f"Error updating Rank Math keyword: {e}")
            return False

    def process_post(self, post):
        """Process a single post for SEO optimization"""
        post_id = post['id']
        post_title = post['title']['rendered']
        post_content = post['content']['rendered']
        post_slug = post['slug']

        report_entry = {
            "post_id": post_id,
            "post_slug": post_slug,
            "original_title": post_title,
            "updated_title": None,
            "meta_description_added": False,
            "keyword_added": False
        }

        try:
            # Check if meta description exists
            meta_description = None
            keyword = None
            meta_description_exists = False
            keyword_exists = False

            # Check for Yoast SEO meta description
            if 'yoast_head_json' in post and post['yoast_head_json'] and 'description' in post['yoast_head_json']:
                meta_description = post['yoast_head_json']['description']
                meta_description_exists = bool(meta_description)

            # Check for Rank Math SEO data
            rank_math_data = self.get_rank_math_data(post_id)
            if rank_math_data:
                # Check for Rank Math meta description
                if not meta_description_exists and 'description' in rank_math_data:
                    meta_description = rank_math_data.get('description', '')
                    meta_description_exists = bool(meta_description)

                # Check for Rank Math focus keyword
                keyword = rank_math_data.get('focus_keyword', '')
                keyword_exists = bool(keyword)

            # If no keyword exists, generate one
            if not keyword_exists:
                self.log(post_id, "No keyword found, generating one...")
                keyword = self.generate_keyword(post_content, post_title)

                if keyword:
                    self.log(post_id, f"Generated keyword: {keyword}")

                    # Update Rank Math keyword
                    if self.update_rank_math_keyword(post_id, keyword):
                        self.log(post_id, "Updated Rank Math keyword")
                        report_entry["keyword_added"] = True
                        keyword_exists = True
                    else:
                        self.log(post_id, "Failed to update Rank Math keyword")

            # If no meta description exists, generate one
            if not meta_description_exists:
                self.log(post_id, "No meta description found, generating one...")
                meta_description = self.generate_meta_description(post_content, keyword)

                if meta_description:
                    self.log(post_id, f"Generated meta description: {meta_description}")
                    report_entry["meta_description_added"] = True
            elif keyword_exists and keyword not in meta_description.lower():
                # If meta description exists but doesn't include the keyword, regenerate it
                self.log(post_id, f"Meta description exists but doesn't include keyword '{keyword}', regenerating...")
                meta_description = self.generate_meta_description(post_content, keyword)

                if meta_description:
                    self.log(post_id, f"Updated meta description: {meta_description}")
                    report_entry["meta_description_added"] = True

            # Update post if needed
            updates_needed = report_entry["keyword_added"] or report_entry["meta_description_added"]

            if keyword_exists and keyword.lower() not in post_title.lower():
                # Update title to include keyword
                new_title = self.update_post_title(post_title, keyword)
                if new_title != post_title:
                    self.log(post_id, f"Updated title: {new_title}")
                    report_entry["updated_title"] = new_title
                    updates_needed = True

            # Prepare update data
            update_data = {}

            if report_entry["updated_title"]:
                update_data["title"] = report_entry["updated_title"]

            if keyword_exists and keyword.lower() not in post_content.lower():
                # Update first paragraph to include keyword
                new_content = self.update_first_paragraph(post_content, keyword)
                if new_content != post_content:
                    self.log(post_id, "Updated first paragraph to include keyword")
                    update_data["content"] = new_content

            if meta_description:
                # Update meta description
                if not rank_math_data:
                    rank_math_data = {}
                rank_math_data["description"] = meta_description

                update_data["meta"] = {
                    "rank_math_data": json.dumps(rank_math_data)
                }

            # Submit updates if needed
            if update_data:
                try:
                    response = requests.post(
                        f"{self.api_url}/posts/{post_id}",
                        json=update_data,
                        auth=self.auth
                    )

                    if response.status_code == 200:
                        self.log(post_id, "Successfully updated post")
                    else:
                        self.log(post_id, f"Failed to update post: {response.status_code} - {response.text}")
                except Exception as e:
                    self.log(post_id, f"Error updating post: {e}")

            # Add to report data
            self.report_data.append(report_entry)

        except Exception as e:
            self.log(post_id, f"Error processing post: {e}")

        return report_entry

    def generate_report(self, filename="wp_seo_optimization_report.csv"):
        """Generate a CSV report of all processed posts"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'post_id', 'post_slug', 'original_title', 'updated_title',
                'meta_description_added', 'keyword_added'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for entry in self.report_data:
                writer.writerow(entry)

        print(f"Report generated: {filename}")

    def generate_error_log(self, filename="wp_seo_optimization_errors.log"):
        """Generate a log file with all errors"""
        with open(filename, 'w', encoding='utf-8') as logfile:
            for entry in self.log_data:
                logfile.write(f"Post {entry['post_id']}: {entry['message']}\n")

        print(f"Error log generated: {filename}")

    def run(self):
        """Run the SEO optimization process on all published posts"""
        print("Starting WordPress SEO optimization...")

        # Get all published posts
        posts = self.get_all_published_posts()

        total_posts = len(posts)
        print(f"Processing {total_posts} posts...")

        # Process each post
        for i, post in enumerate(posts):
            print(f"\nProcessing post {i + 1}/{total_posts} (ID: {post['id']})...")
            self.process_post(post)
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)

        # Generate report and error log
        self.generate_report()
        self.generate_error_log()

        print("\nSEO optimization completed!")
        print(f"Total posts processed: {total_posts}")
        print(f"Posts with added meta descriptions: {sum(1 for r in self.report_data if r['meta_description_added'])}")
        print(f"Posts with added keywords: {sum(1 for r in self.report_data if r['keyword_added'])}")
        print(f"Posts with updated titles: {sum(1 for r in self.report_data if r['updated_title'])}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='WordPress SEO Optimizer')
    parser.add_argument('--url', required=True, help='WordPress site URL')
    parser.add_argument('--username', required=True, help='WordPress username')
    parser.add_argument('--password', required=True, help='WordPress application password')
    parser.add_argument('--gemini-api-key', required=True, help='Google Gemini API key')

    args = parser.parse_args()

    optimizer = WordPressSEOOptimizer(
        base_url=args.url,
        username=args.username,
        app_password=args.password,
        gemini_api_key=args.gemini_api_key
    )

    optimizer.run()