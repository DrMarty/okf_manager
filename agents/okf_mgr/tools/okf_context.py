from __future__ import annotations

from helpers.tool import Tool, Response

class OkfContext(Tool):
    """Set or inspect session-local OKF tool context for profile tools."""

    async def execute(self, **kwargs):
        action = self.args.get("action", "show")
        data = self.agent.get_data("okf_context") or {}
        if action == "set":
            for key in ("bundle_root", "source", "dataset", "billing_project"):
                if key in self.args and self.args[key] is not None:
                    data[key] = self.args[key]
            self.agent.set_data("okf_context", data)
            return Response(message=f"OKF context set: {data}", break_loop=False)
        if action == "clear":
            self.agent.set_data("okf_context", {})
            return Response(message="OKF context cleared.", break_loop=False)
        return Response(message=f"OKF context: {data}", break_loop=False)
