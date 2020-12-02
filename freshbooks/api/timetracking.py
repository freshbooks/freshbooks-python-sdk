from freshbooks.api.projects import ProjectsResource


class TimetrackingResource(ProjectsResource):
    """Handles resources under the `/timetracking` endpoints.

    These are handled identically to `/projects` endpoints.
    Refer to `freshbooks.api.projects.ProjectsResource`.
    """

    def _get_url(self, business_id, resource_id=None):
        if resource_id:
            return "{}/timetracking/business/{}/{}/{}".format(
                self.base_url, business_id, self.resource_path, resource_id
            )
        return "{}/timetracking/business/{}/{}".format(self.base_url, business_id, self.resource_path)
