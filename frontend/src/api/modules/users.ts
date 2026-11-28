import { apiRequest } from '../client/http';

export type TeamRole = 'admin' | 'operator' | 'customer';

export interface UserInvitation {
  email: string;
  fullName: string;
  role: TeamRole;
}

interface UserInvitationResponse {
  data: UserInvitation;
  message: string;
}

export async function inviteTeamMember(input: UserInvitation): Promise<UserInvitationResponse> {
  return apiRequest<UserInvitationResponse>('/api/v1/users/invitations', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}
