from typing import Dict, Any, Optional, Callable
from datetime import datetime

from config import config
from utils.agent_utils import save_to_file
from utils.agent_runner import run_agent_with_runner
from utils.workflow_utils import (
    WorkflowState,
    WorkflowStatus,
    RetryHelper,
    format_workflow_report,
    log_workflow_step,
)

class SupervisorAgent:
    """
    Supervisor Agent that orchestrates the entire AI-Curation workflow.
    
    Responsibilities:
    - Coordinate news gathering, social media monitoring, and content generation
    - Manage workflow state and progress
    - Implement retry logic with exponential backoff
    - Handle errors gracefully
    - Save intermediate and final results
    - Generate comprehensive workflow reports
    """
    
    def __init__(self):
        self.workflow_state = WorkflowState()
        self.config = config
        
        # Initialize workflow steps
        self._initialize_workflow()
    
    def _initialize_workflow(self):
        """Initialize workflow steps"""
        self.workflow_state.add_step(
            "news_gathering",
            "Gather latest news articles and events"
        )
        self.workflow_state.add_step(
            "social_media_monitoring",
            "Monitor social media accounts for relevant posts"
        )
        self.workflow_state.add_step(
            "content_generation",
            "Generate publication-ready content"
        )
        self.workflow_state.add_step(
            "final_output",
            "Compile and save final outputs"
        )
    
    async def execute_with_retry(
        self,
        step_name: str,
        agent_executor: Callable,
        agent_name: str,
        state: Dict[str, Any] = None,
        max_retries: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute an agent with retry logic.
        
        Args:
            step_name: Name of the workflow step
            agent_executor: Function to execute the agent
            agent_name: Display name of the agent
            state: Initial state for the agent
            max_retries: Maximum retry attempts (defaults to config)
            
        Returns:
            Agent results or None if failed
        """
        if max_retries is None:
            max_retries = self.config.max_retries
        
        if state is None:
            state = {}
        
        for attempt in range(1, max_retries + 1):
            try:
                log_workflow_step(
                    step_name,
                    f"Executing {agent_name} (Attempt {attempt}/{max_retries})",
                    "INFO"
                )
                
                self.workflow_state.start_step(step_name, attempt)
                
                # Execute the agent
                result = await agent_executor(state)
                
                # Check if result is valid
                if result and (isinstance(result, dict) or isinstance(result, str)):
                    log_workflow_step(
                        step_name,
                        f"{agent_name} completed successfully",
                        "SUCCESS"
                    )
                    self.workflow_state.complete_step(step_name, result)
                    
                    # Save intermediate results if configured
                    if self.config.save_intermediate_results:
                        self._save_intermediate_result(step_name, result)
                    
                    return result
                else:
                    raise ValueError("Agent returned no valid results")
                
            except Exception as e:
                error_msg = f"{agent_name} failed: {str(e)}"
                log_workflow_step(step_name, error_msg, "ERROR")
                
                # Check if should retry
                if attempt < max_retries and RetryHelper.should_retry(attempt, max_retries, e):
                    self.workflow_state.retry_step(step_name)
                    log_workflow_step(
                        step_name,
                        f"Retrying {agent_name}... ({attempt + 1}/{max_retries})",
                        "WARNING"
                    )
                    RetryHelper.wait_before_retry(attempt, self.config.retry_delay)
                else:
                    # Max retries reached or non-retriable error
                    self.workflow_state.complete_step(step_name, error=error_msg)
                    
                    if not self.config.continue_on_failure:
                        log_workflow_step(
                            step_name,
                            "Workflow terminated due to failure",
                            "ERROR"
                        )
                        raise
                    
                    log_workflow_step(
                        step_name,
                        "Continuing workflow despite failure",
                        "WARNING"
                    )
                    return None
        
        return None
    
    def _save_intermediate_result(self, step_name: str, result: Any):
        """Save intermediate result to file"""
        try:
            import os
            os.makedirs(self.config.output_directory, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{step_name}_{timestamp}.json"
            
            import json
            filepath = os.path.join(self.config.output_directory, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)
            
            log_workflow_step(
                step_name,
                f"Intermediate result saved to {filename}",
                "INFO"
            )
        except Exception as e:
            log_workflow_step(
                step_name,
                f"Failed to save intermediate result: {e}",
                "WARNING"
            )
    
    async def run_news_gathering(self) -> Optional[Dict[str, Any]]:
        """Execute news gathering step"""
        from agents.news_gatherer import news_gathering_agent
        
        async def executor(agent_state):
            return await run_agent_with_runner(
                news_gathering_agent,
                "News Gathering Agent",
                agent_state,
            )
        
        state = {
            "keywords": self.config.search_keywords,
            "resource_links": self.config.resource_links,
            "max_items": self.config.max_news_items,
            "timestamp": datetime.now().isoformat(),
        }
        
        return await self.execute_with_retry(
            "news_gathering",
            executor,
            "News Gathering Agent",
            state
        )
    
    async def run_social_media_monitoring(self) -> Optional[Dict[str, Any]]:
        """Execute social media monitoring step"""
        from agents.social_media_watch import social_media_monitoring_agent
        
        async def executor(agent_state):
            return await run_agent_with_runner(
                social_media_monitoring_agent,
                "Social Media Monitoring Agent",
                agent_state,
            )
        
        state = {
            "accounts": self.config.social_media_accounts,
            "keywords": self.config.social_media_keywords,
            "max_posts": self.config.max_posts_per_account,
            "lookback_days": self.config.social_media_lookback_days,
            "timestamp": datetime.now().isoformat(),
        }
        
        return await self.execute_with_retry(
            "social_media_monitoring",
            executor,
            "Social Media Monitoring Agent",
            state
        )
    
    async def run_content_generation(
        self,
        news_results: Optional[Dict[str, Any]],
        social_results: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Execute content generation step"""
        from agents.content_generator import content_generation_orchestrator
        
        async def executor(agent_state):
            return await run_agent_with_runner(
                content_generation_orchestrator,
                "Content Generation Agent",
                agent_state,
            )
        
        # Prepare state with gathered information
        state = {
            "gathered_news": news_results.get("curated_content", "") if news_results else "",
            "gathered_posts": social_results.get("social_media_report", "") if social_results else "",
            "social_media_analysis": social_results.get("analysis", "") if social_results else "",
            "brand_name": self.config.brand_name,
            "brand_tagline": self.config.brand_tagline,
            "brand_voice": self.config.brand_voice,
            "target_audience": self.config.target_audience,
            "preferred_content_type": self.config.default_content_type,
            "summary_length": self.config.summary_length,
            "blog_post_length": self.config.blog_post_length,
            "include_seo": self.config.include_seo,
            "include_cta": self.config.include_cta,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Check if we have any input
        if not news_results and not social_results:
            log_workflow_step(
                "content_generation",
                "No input data available, skipping content generation",
                "WARNING"
            )
            self.workflow_state.skip_step(
                "content_generation",
                "No input data from previous steps"
            )
            return None
        
        return await self.execute_with_retry(
            "content_generation",
            executor,
            "Content Generation Agent",
            state
        )
    
    def compile_final_output(
        self,
        news_results: Optional[Dict[str, Any]],
        social_results: Optional[Dict[str, Any]],
        content_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compile all results into final output"""
        log_workflow_step("final_output", "Compiling final outputs", "INFO")
        
        self.workflow_state.start_step("final_output")
        
        final_output = {
            "workflow_id": self.workflow_state.workflow_id,
            "generated_at": datetime.now().isoformat(),
            "brand": self.config.brand_name,
            "components": {},
            "files": [],
        }
        
        # Add news results
        if news_results:
            final_output["components"]["news"] = {
                "status": "success",
                "summary": "News gathering completed",
            }
        
        # Add social media results
        if social_results:
            final_output["components"]["social_media"] = {
                "status": "success",
                "summary": "Social media monitoring completed",
            }
        
        # Add content generation results
        if content_results:
            final_output["components"]["content"] = {
                "status": "success",
                "summary": "Content generation completed",
            }
        
        # Save all outputs
        try:
            import os
            os.makedirs(self.config.content_output_directory, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save main content if available
            if content_results:
                for key in ['generated_content', 'blog_post', 'final_content']:
                    if key in content_results:
                        filepath = save_to_file(
                            content_results[key],
                            f"final_content_{timestamp}.md",
                            self.config.content_output_directory
                        )
                        final_output["files"].append(filepath)
                        log_workflow_step("final_output", f"Saved: {filepath}", "SUCCESS")
                        break
            
            # Save workflow report
            report = format_workflow_report(self.workflow_state)
            report_path = save_to_file(
                report,
                f"workflow_report_{timestamp}.md",
                self.config.workflow_logs_directory
            )
            final_output["files"].append(report_path)
            final_output["workflow_report"] = report_path
            
            # Save workflow state
            state_path = self.workflow_state.save_to_file(self.config.workflow_logs_directory)
            final_output["files"].append(state_path)
            final_output["workflow_state"] = state_path
            
            self.workflow_state.complete_step("final_output", final_output)
            log_workflow_step("final_output", "All outputs compiled successfully", "SUCCESS")
            
        except Exception as e:
            error_msg = f"Failed to save final outputs: {e}"
            self.workflow_state.complete_step("final_output", error=error_msg)
            log_workflow_step("final_output", error_msg, "ERROR")
        
        return final_output
    
    async def run_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete AI-Curation workflow.
        
        Returns:
            Dictionary containing all results and metadata
        """
        print("\n" + "="*70)
        print("  🚀 AI-CURATION WORKFLOW STARTING")
        print("="*70 + "\n")
        
        self.workflow_state.start_workflow()
        
        news_results = None
        social_results = None
        content_results = None
        
        try:
            # Step 1: News Gathering
            print("\n" + "─"*70)
            print("  📰 STEP 1/3: NEWS GATHERING")
            print("─"*70)
            
            news_results = await self.run_news_gathering()
            
            if news_results:
                print(f"  ✅ News gathering completed")
            else:
                print(f"  ⚠️  News gathering failed or returned no results")
            
            # Step 2: Social Media Monitoring
            print("\n" + "─"*70)
            print("  📱 STEP 2/3: SOCIAL MEDIA MONITORING")
            print("─"*70)
            
            social_results = await self.run_social_media_monitoring()
            
            if social_results:
                print(f"  ✅ Social media monitoring completed")
            else:
                print(f"  ⚠️  Social media monitoring failed or returned no results")
            
            # Step 3: Content Generation
            print("\n" + "─"*70)
            print("  ✍️  STEP 3/3: CONTENT GENERATION")
            print("─"*70)
            
            content_results = await self.run_content_generation(news_results, social_results)
            
            if content_results:
                print(f"  ✅ Content generation completed")
            else:
                print(f"  ⚠️  Content generation failed or returned no results")
            
            # Determine overall workflow status
            if content_results:
                workflow_status = WorkflowStatus.SUCCESS
            elif news_results or social_results:
                workflow_status = WorkflowStatus.PARTIAL
            else:
                workflow_status = WorkflowStatus.FAILED
            
            self.workflow_state.complete_workflow(workflow_status)
            
        except Exception as e:
            log_workflow_step("workflow", f"Critical error: {e}", "ERROR")
            self.workflow_state.complete_workflow(WorkflowStatus.FAILED)
            import traceback
            traceback.print_exc()
        
        # Compile final output
        print("\n" + "─"*70)
        print("  📦 COMPILING FINAL OUTPUTS")
        print("─"*70)
        
        final_output = self.compile_final_output(news_results, social_results, content_results)
        
        # Print summary
        self._print_workflow_summary()
        
        return final_output
    
    def _print_workflow_summary(self):
        """Print workflow execution summary"""
        summary = self.workflow_state.get_summary()
        
        print("\n" + "="*70)
        print("  ✨ WORKFLOW EXECUTION SUMMARY")
        print("="*70)
        
        print(f"\n  Workflow ID: {summary['workflow_id']}")
        print(f"  Status: {summary['status'].upper()}")
        print(f"  Duration: {summary['duration']:.2f} seconds ({summary['duration']/60:.1f} minutes)")
        
        print(f"\n  📊 Steps:")
        print(f"     Total: {summary['total_steps']}")
        print(f"     Completed: {summary['completed_steps']} ✅")
        print(f"     Failed: {summary['failed_steps']} ❌")
        print(f"     Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\n  📁 Output Files:")
        print(f"     Content: {self.config.content_output_directory}/")
        print(f"     Logs: {self.config.workflow_logs_directory}/")
        
        if self.workflow_state.errors:
            print(f"\n  ⚠️  Errors: {len(self.workflow_state.errors)}")
            for error in self.workflow_state.errors[:3]:  # Show first 3
                print(f"     - {error['step']}: {error['error'][:60]}...")
        
        print("\n" + "="*70 + "\n")

# Create supervisor instance
supervisor = SupervisorAgent()