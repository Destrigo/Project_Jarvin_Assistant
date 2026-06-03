"""Google Tasks integration — list and create tasks."""
from googleapiclient.discovery import build
from integrations.google_auth import get_credentials


def _service():
    return build("tasks", "v1", credentials=get_credentials())


def tasks_list(max_results: int = 20, include_completed: bool = False) -> dict:
    """List tasks from all Google Task lists."""
    svc = _service()

    # get all task lists
    lists_resp = svc.tasklists().list(maxResults=10).execute()
    task_lists = lists_resp.get("items", [])

    all_tasks = []
    for tl in task_lists:
        tl_id = tl["id"]
        tl_title = tl["title"]
        kwargs: dict = {
            "tasklist": tl_id,
            "maxResults": max_results,
            "showCompleted": include_completed,
            "showHidden": False,
        }
        resp = svc.tasks().list(**kwargs).execute()
        for t in resp.get("items", []):
            if not include_completed and t.get("status") == "completed":
                continue
            all_tasks.append({
                "id":        t["id"],
                "title":     t.get("title", ""),
                "status":    t.get("status", "needsAction"),
                "due":       t.get("due", ""),
                "notes":     t.get("notes", ""),
                "list":      tl_title,
                "list_id":   tl_id,
            })

    all_tasks.sort(key=lambda t: t["due"] or "9999")
    return {"tasks": all_tasks, "count": len(all_tasks), "task_lists": [tl["title"] for tl in task_lists]}


def tasks_create(title: str, tasklist_id: str = "@default",
                 due: str = "", notes: str = "") -> dict:
    """Create a Google Task.

    tasklist_id: use '@default' for the default list, or pass a list ID from tasks_list
    due: ISO 8601 date-time string, e.g. '2025-06-10T00:00:00.000Z'
    """
    svc = _service()
    body: dict = {"title": title, "status": "needsAction"}
    if due:
        body["due"] = due
    if notes:
        body["notes"] = notes

    task = svc.tasks().insert(tasklist=tasklist_id, body=body).execute()
    return {
        "id":       task["id"],
        "title":    task.get("title", ""),
        "due":      task.get("due", ""),
        "list_id":  tasklist_id,
        "status":   task.get("status", "needsAction"),
    }


def tasks_complete(task_id: str, tasklist_id: str = "@default") -> dict:
    """Mark a task as completed."""
    svc = _service()
    task = svc.tasks().patch(
        tasklist=tasklist_id,
        task=task_id,
        body={"status": "completed"},
    ).execute()
    return {"id": task["id"], "title": task.get("title", ""), "status": task.get("status", "")}
