import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing Hackathon Review API")
    print("=" * 40)
    
    # 1. Check API health
    print("1. Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("API is healthy")
    else:
        print("API is not responding")
        return
    
    # 2. Create a project
    print("\n2. Creating project...")
    project_data = {
        "hackathon_id": "TestHack2025",
        "name": "Test AI Health App",
        "description": "A simple AI health application for testing the review system. This app helps patients manage their medications and track symptoms.",
        "work_done": "We built a basic prototype with user registration, medication tracking, and simple analytics dashboard."
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/projects", json=project_data)
    if response.status_code == 201:
        project = response.json()
        project_id = project['project_id']
        print(f"Created project: {project_id}")
    else:
        print(f"Failed to create project: {response.text}")
        return
    
    # 3. Submit a review
    print("\n3. Submitting review...")
    review_data = {
        "reviewer_name": "Dr. Test Reviewer",
        "text_review": "This is a promising healthcare application. The medication tracking feature could be very useful for patients. However, more work is needed on data security and clinical validation.",
        "confidence_score": 85
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/reviews", json=review_data)
    if response.status_code == 201:
        review = response.json()
        print(f"Submitted review: {review['review_id']}")
    else:
        print(f"Failed to submit review: {response.text}")
        return
    
    # 4. Start processing
    print("\n4. Starting processing...")
    process_options = {
        "generate_artificial_reviews": True,
        "force_reprocess": False
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/process", json=process_options)
    if response.status_code == 202:
        job = response.json()
        print(f"Processing started: {job['processing_job_id']}")
    else:
        print(f"Failed to start processing: {response.text}")
        return
    
    # 5. Wait for processing to complete
    print("\n5. Waiting for processing to complete...")
    max_attempts = 60  # Maximum 5 minutes (60 * 5 seconds)
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/status")
        if response.status_code == 200:
            status = response.json()
            current_status = status['status']
            steps_completed = status['progress']['steps_completed']
            total_steps = status['progress']['total_steps']
            current_step = status['progress']['current_step']
            
            print(f"Status: {current_status} - {current_step} ({steps_completed}/{total_steps})")
            
            # Check if completed or failed
            if current_status == 'completed':
                print("Processing completed")
                break
            elif current_status == 'failed':
                print("Processing failed")
                errors = status.get('errors', [])
                if errors:
                    print(f"Errors: {errors}")
                break
            else:
                # Still processing, wait and try again
                time.sleep(5)
                attempt += 1
        else:
            print(f"Failed to get status: {response.text}")
            break
    
    if attempt >= max_attempts:
        print("⚠ Timeout waiting for processing to complete")
    
    # 6. Get feedback report
    print("\n6. Getting feedback report...")
    response = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/feedback")
    if response.status_code == 200:
        feedback = response.json()
        print(f"Got feedback report")
        print(f"Overall Score: {feedback['overall_score']}/5.0")
        print(f"Generated at: {feedback['generated_at']}")
        
        # Show dimension scores
        print("\nDimension Scores:")
        for dimension, score in feedback['feedback_scores'].items():
            print(f"  - {dimension.replace('_', ' ').title()}: {score}/5.0")
    else:
        print(f"Failed to get feedback: {response.text}")
    
    print(f"\nTest completed")
    print(f"Project ID: {project_id}")

if __name__ == "__main__":
    try:
        test_api()
    except requests.RequestException as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"Error: {e}")