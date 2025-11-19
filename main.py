
import sys
import asyncio
from datetime import datetime

from agents.supervisor import supervisor
from config import config

def print_configuration():
    """Print current configuration"""
    print("\n⚙️  Configuration:")
    print(f"   • Model: {config.worker_model}")
    print(f"   • Max Retries: {config.max_retries}")
    print(f"   • Continue on Failure: {config.continue_on_failure}")
    print(f"   • Save Intermediate Results: {config.save_intermediate_results}")
    print(f"   • News Items: {config.max_news_items}")
    print(f"   • Social Posts per Account: {config.max_posts_per_account}")
    print(f"   • Content Length: {config.blog_post_length}")

def display_menu():
    """Display main menu"""
    print("\n" + "="*70)
    print("  MAIN MENU")
    print("="*70)
    print("\n  1. 🚀 Run Complete Workflow (Recommended)")
    print("  2. 📋 View Configuration")
    print("  3. 📊 View Last Workflow Report")
    print("  4. 🔧 Advanced Options")
    print("  5. ❌ Exit")
    
    choice = input("\n  Enter your choice (1-5): ").strip()
    return choice

def advanced_menu():
    """Display advanced options menu"""
    print("\n" + "="*70)
    print("  ADVANCED OPTIONS")
    print("="*70)
    print("\n  1. 📰 Run News Gathering Only")
    print("  2. 📱 Run Social Media Monitoring Only")
    print("  3. ✍️  Run Content Generation Only")
    print("  4. 🔙 Back to Main Menu")
    
    choice = input("\n  Enter your choice (1-4): ").strip()
    return choice

async def run_complete_workflow():
    """Run the complete AI-Curation workflow"""
    print("\n" + "🎬 " + "="*68)
    print("  STARTING COMPLETE AI-CURATION WORKFLOW")
    print("  " + "="*68)
    
    print(f"\n  ⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n  This workflow will:")
    print(f"     1. Gather latest news and events")
    print(f"     2. Monitor social media accounts")
    print(f"     3. Generate publication-ready content")
    print(f"     4. Save all outputs and reports")
    
    print(f"\n  ⚡ Each step will retry up to {config.max_retries} times on failure")
    
    input("\n  Press Enter to begin...")
    
    # Run the supervisor
    results = await supervisor.run_workflow()
    
    return results

def view_last_report():
    """View the last workflow report"""
    print("\n" + "="*70)
    print("  LAST WORKFLOW REPORT")
    print("="*70 + "\n")
    
    import os
    import glob
    
    # Find most recent report
    reports = glob.glob(os.path.join(config.workflow_logs_directory, "workflow_report_*.md"))
    
    if not reports:
        print("  ⚠️  No workflow reports found.")
        print(f"     Run a workflow first to generate a report.")
        return
    
    latest_report = max(reports, key=os.path.getctime)
    
    print(f"  📄 Report: {os.path.basename(latest_report)}\n")
    
    try:
        with open(latest_report, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"  ❌ Error reading report: {e}")

async def run_single_step(step: str):
    """Run a single workflow step"""
    print(f"\n  Running {step}...")
    
    if step == "news":
        results = await supervisor.run_news_gathering()
    elif step == "social":
        results = await supervisor.run_social_media_monitoring()
    elif step == "content":
        print("  ⚠️  Content generation requires previous steps to have data.")
        print("  Please run the complete workflow instead.")
        return None
    
    if results:
        print(f"  ✅ {step.title()} completed successfully")
        
        # Save result
        from agent_utils import save_to_file
        import json
        
        filepath = save_to_file(
            json.dumps(results, indent=2, default=str),
            f"{step}_results.json",
            config.output_directory
        )
        print(f"  💾 Results saved to: {filepath}")
    else:
        print(f"  ❌ {step.title()} failed")
    
    return results

async def main_async():
    """Async main function"""
    
    # Check configuration
    if not config.worker_model:
        print("\n  ❌ Error: WORKER_MODEL not configured")
        print("     Please set up your .env file with required configuration.")
        sys.exit(1)
    
    while True:
        choice = display_menu()
        
        if choice == '1':
            # Run complete workflow
            await run_complete_workflow()
            input("\n  Press Enter to continue...")
            
        elif choice == '2':
            # View configuration
            print_configuration()
            input("\n  Press Enter to continue...")
            
        elif choice == '3':
            # View last report
            view_last_report()
            input("\n  Press Enter to continue...")
            
        elif choice == '4':
            # Advanced options
            while True:
                adv_choice = advanced_menu()
                
                if adv_choice == '1':
                    await run_single_step("news")
                    input("\n  Press Enter to continue...")
                elif adv_choice == '2':
                    await run_single_step("social")
                    input("\n  Press Enter to continue...")
                elif adv_choice == '3':
                    await run_single_step("content")
                    input("\n  Press Enter to continue...")
                elif adv_choice == '4':
                    break
                else:
                    print("\n  ⚠️  Invalid choice.")
            
        elif choice == '5':
            # Exit
            print("\n  👋 Thank you for using AI-Curation System!")
            print(f"  💚 {config.brand_name}\n")
            break
            
        else:
            print("\n  ⚠️  Invalid choice. Please try again.")

def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Workflow interrupted by user.")
        print("  👋 Goodbye!\n")
    except Exception as e:
        print(f"\n  ❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()