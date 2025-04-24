# WordPress SEO Optimizer

This Python script connects to a WordPress site using Application Passwords and optimizes published posts for SEO.  
It uses the Google Gemini API to generate meta descriptions and keyword phrases, and updates posts to improve their SEO performance.

## Features

- **Fetch All Published Posts:**  
  Retrieves all published posts from your WordPress site using the REST API.

- **Meta Description Generation:**  
  Uses Google Gemini to generate a compelling meta description for each post if one does not exist, or if the existing one does not include the focus keyword.

- **Keyword Generation:**  
  Uses Google Gemini to generate a relevant 2-3 word SEO keyword phrase for each post if one does not exist.

- **Title Optimization:**  
  Updates the post title to include the focus keyword if it is not already present, while maintaining readability.

- **First Paragraph Optimization:**  
  Updates the first paragraph of the post content to include the focus keyword if it is not already present.

- **Rank Math SEO Integration:**  
  Reads and updates Rank Math SEO meta fields, including the focus keyword and meta description.

- **Yoast SEO Meta Detection:**  
  Detects existing Yoast SEO meta descriptions to avoid unnecessary overwrites.

- **Reporting:**  
  Generates a CSV report (`wp_seo_optimization_report.csv`) summarizing which posts had meta descriptions, keywords, or titles updated.

- **Error Logging:**  
  Generates a log file (`wp_seo_optimization_errors.log`) with details of any errors encountered during processing.

- **Command-Line Interface:**  
  Accepts WordPress credentials and Gemini API key as command-line arguments.

## Usage

1. **Install dependencies:**
   ```bash
   pip install requests google-generativeai
   ```

2. **Run the script:**
   ```bash
   python main.py --url <WORDPRESS_URL> --username <USERNAME> --password <APP_PASSWORD> --gemini-api-key <GEMINI_API_KEY>
   ```

   - `<WORDPRESS_URL>`: Your WordPress site URL (e.g., `https://example.com`)
   - `<USERNAME>`: Your WordPress username
   - `<APP_PASSWORD>`: Your WordPress application password (see [WordPress Application Passwords](https://wordpress.org/support/article/application-passwords/))
   - `<GEMINI_API_KEY>`: Your Google Gemini API key

3. **Output:**
   - `wp_seo_optimization_report.csv`: Summary of SEO changes per post
   - `wp_seo_optimization_errors.log`: Error log

## Requirements

- Python 3.x
- [requests](https://pypi.org/project/requests/)
- [google-generativeai](https://pypi.org/project/google-generativeai/)

## Notes

- The script is designed to work with WordPress sites using either Rank Math or Yoast SEO plugins.
- It uses the WordPress REST API and requires an Application Password for authentication.
- The Google Gemini API is used for generating meta descriptions and keywords.

## License

MIT License
