/**
 * RLS (Row Level Security) Isolation Tests
 *
 * These tests verify that Row Level Security policies properly isolate
 * data between different users and organizations, preventing unauthorized access.
 *
 * Critical Security Test Suite - Phase 1
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.SUPABASE_URL || 'http://localhost:54321'
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || ''

// Test users
const TEST_USER_A = {
  email: 'test-user-a@example.com',
  password: 'TestPassword123!',
  id: '',
  token: ''
}

const TEST_USER_B = {
  email: 'test-user-b@example.com',
  password: 'TestPassword123!',
  id: '',
  token: ''
}

describe('RLS Isolation Tests', () => {
  let serviceClient: SupabaseClient
  let userAClient: SupabaseClient
  let userBClient: SupabaseClient

  beforeAll(async () => {
    // Create service role client (bypasses RLS)
    serviceClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    // Create test users
    const { data: userA, error: errorA } = await serviceClient.auth.admin.createUser({
      email: TEST_USER_A.email,
      password: TEST_USER_A.password,
      email_confirm: true
    })

    if (errorA) throw new Error(`Failed to create User A: ${errorA.message}`)
    TEST_USER_A.id = userA.user?.id || ''

    const { data: userB, error: errorB } = await serviceClient.auth.admin.createUser({
      email: TEST_USER_B.email,
      password: TEST_USER_B.password,
      email_confirm: true
    })

    if (errorB) throw new Error(`Failed to create User B: ${errorB.message}`)
    TEST_USER_B.id = userB.user?.id || ''

    // Sign in users
    const signInA = await serviceClient.auth.signInWithPassword({
      email: TEST_USER_A.email,
      password: TEST_USER_A.password
    })
    if (signInA.error) throw new Error(`Failed to sign in User A: ${signInA.error.message}`)
    TEST_USER_A.token = signInA.data.session?.access_token || ''

    const signInB = await serviceClient.auth.signInWithPassword({
      email: TEST_USER_B.email,
      password: TEST_USER_B.password
    })
    if (signInB.error) throw new Error(`Failed to sign in User B: ${signInB.error.message}`)
    TEST_USER_B.token = signInB.data.session?.access_token || ''

    // Create authenticated clients
    userAClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      global: {
        headers: {
          Authorization: `Bearer ${TEST_USER_A.token}`
        }
      }
    })

    userBClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      global: {
        headers: {
          Authorization: `Bearer ${TEST_USER_B.token}`
        }
      }
    })

    // Create blog authors for both users
    await serviceClient.from('blog_authors').insert([
      {
        user_id: TEST_USER_A.id,
        name: 'Test Author A',
        slug: 'test-author-a',
        email: TEST_USER_A.email
      },
      {
        user_id: TEST_USER_B.id,
        name: 'Test Author B',
        slug: 'test-author-b',
        email: TEST_USER_B.email
      }
    ])
  })

  afterAll(async () => {
    // Clean up test data
    await serviceClient.auth.admin.deleteUser(TEST_USER_A.id)
    await serviceClient.auth.admin.deleteUser(TEST_USER_B.id)
    await serviceClient.from('blog_authors').delete().eq('email', TEST_USER_A.email)
    await serviceClient.from('blog_authors').delete().eq('email', TEST_USER_B.email)
  })

  describe('Blog Posts RLS', () => {
    it('should prevent User B from reading User A draft posts', async () => {
      // Get User A's author ID
      const { data: authorA } = await serviceClient
        .from('blog_authors')
        .select('id')
        .eq('user_id', TEST_USER_A.id)
        .single()

      if (!authorA) throw new Error('Author A not found')

      // User A creates a draft post
      const { data: draftPost } = await serviceClient
        .from('blog_posts')
        .insert({
          title: 'User A Draft Post',
          slug: 'user-a-draft-' + Date.now(),
          content: 'This is a draft post',
          author_id: authorA.id,
          status: 'draft'
        })
        .select()
        .single()

      // User B tries to read the draft
      const { data: readAttempt, error } = await userBClient
        .from('blog_posts')
        .select()
        .eq('id', draftPost?.id)

      // Should not be able to read User A's draft
      expect(readAttempt).toEqual([])
      expect(error).toBeNull()
    })

    it('should allow User B to read User A published posts', async () => {
      // Get User A's author ID
      const { data: authorA } = await serviceClient
        .from('blog_authors')
        .select('id')
        .eq('user_id', TEST_USER_A.id)
        .single()

      if (!authorA) throw new Error('Author A not found')

      // User A creates a published post
      const { data: publishedPost } = await serviceClient
        .from('blog_posts')
        .insert({
          title: 'User A Published Post',
          slug: 'user-a-published-' + Date.now(),
          content: 'This is a published post',
          author_id: authorA.id,
          status: 'published',
          published_at: new Date().toISOString()
        })
        .select()
        .single()

      // User B tries to read the published post
      const { data: readAttempt, error } = await userBClient
        .from('blog_posts')
        .select()
        .eq('id', publishedPost?.id)

      // Should be able to read published posts
      expect(readAttempt).toHaveLength(1)
      expect(readAttempt?.[0]?.title).toBe('User A Published Post')
      expect(error).toBeNull()
    })

    it('should prevent User B from updating User A posts', async () => {
      // Get User A's author ID
      const { data: authorA } = await serviceClient
        .from('blog_authors')
        .select('id')
        .eq('user_id', TEST_USER_A.id)
        .single()

      if (!authorA) throw new Error('Author A not found')

      // Create a post as User A
      const { data: post } = await serviceClient
        .from('blog_posts')
        .insert({
          title: 'User A Post to Update',
          slug: 'user-a-update-' + Date.now(),
          content: 'Original content',
          author_id: authorA.id,
          status: 'published',
          published_at: new Date().toISOString()
        })
        .select()
        .single()

      // User B tries to update User A's post
      const { error } = await userBClient
        .from('blog_posts')
        .update({ content: 'Hacked content' })
        .eq('id', post?.id)

      // Should fail with RLS error
      expect(error).not.toBeNull()
      expect(error?.code).toBe('42501') // insufficient_privilege
    })

    it('should prevent User B from deleting User A posts', async () => {
      // Get User A's author ID
      const { data: authorA } = await serviceClient
        .from('blog_authors')
        .select('id')
        .eq('user_id', TEST_USER_A.id)
        .single()

      if (!authorA) throw new Error('Author A not found')

      // Create a post as User A
      const { data: post } = await serviceClient
        .from('blog_posts')
        .insert({
          title: 'User A Post to Delete',
          slug: 'user-a-delete-' + Date.now(),
          content: 'Content to delete',
          author_id: authorA.id,
          status: 'published',
          published_at: new Date().toISOString()
        })
        .select()
        .single()

      // User B tries to delete User A's post
      const { error } = await userBClient
        .from('blog_posts')
        .delete()
        .eq('id', post?.id)

      // Should fail with RLS error
      expect(error).not.toBeNull()
      expect(error?.code).toBe('42501') // insufficient_privilege
    })
  })

  describe('Blog Comments RLS', () => {
    it('should allow anyone to read approved comments', async () => {
      // Create a post and comment
      const { data: post } = await serviceClient
        .from('blog_posts')
        .insert({
          title: 'Post with Comments',
          slug: 'post-comments-' + Date.now(),
          content: 'Content',
          status: 'published',
          published_at: new Date().toISOString()
        })
        .select()
        .single()

      const { data: comment } = await serviceClient
        .from('blog_comments')
        .insert({
          post_id: post?.id,
          author_name: 'Test Commenter',
          author_email: 'commenter@example.com',
          content: 'Test comment',
          status: 'approved'
        })
        .select()
        .single()

      // User B tries to read the comment
      const { data: readAttempt, error } = await userBClient
        .from('blog_comments')
        .select()
        .eq('id', comment?.id)

      // Should be able to read approved comments
      expect(readAttempt).toHaveLength(1)
      expect(error).toBeNull()
    })

    it('should prevent reading pending comments', async () => {
      // Create a pending comment
      const { data: post } = await serviceClient
        .from('blog_posts')
        .insert({
          title: 'Post with Pending Comment',
          slug: 'post-pending-' + Date.now(),
          content: 'Content',
          status: 'published',
          published_at: new Date().toISOString()
        })
        .select()
        .single()

      const { data: comment } = await serviceClient
        .from('blog_comments')
        .insert({
          post_id: post?.id,
          author_name: 'Pending Commenter',
          author_email: 'pending@example.com',
          content: 'Pending comment',
          status: 'pending'
        })
        .select()
        .single()

      // User B tries to read the pending comment
      const { data: readAttempt } = await userBClient
        .from('blog_comments')
        .select()
        .eq('id', comment?.id)

      // Should not be able to read pending comments
      expect(readAttempt).toEqual([])
    })
  })

  describe('Fractal Agents RLS', () => {
    it('should isolate agents by organization_id', async () => {
      // Create agents for both organizations
      const { data: agentA } = await serviceClient
        .from('fractal_agents')
        .insert({
          name: 'Agent A',
          type: 'specialist',
          organization_id: TEST_USER_A.id,
          description: 'Test agent for Org A'
        })
        .select()
        .single()

      const { data: agentB } = await serviceClient
        .from('fractal_agents')
        .insert({
          name: 'Agent B',
          type: 'specialist',
          organization_id: TEST_USER_B.id,
          description: 'Test agent for Org B'
        })
        .select()
        .single()

      // User A tries to read Agent B
      const { data: readAttempt } = await userAClient
        .from('fractal_agents')
        .select()
        .eq('id', agentB?.id)

      // Should not be able to read other org's agents
      expect(readAttempt).toEqual([])
    })

    it('should allow reading agents with null organization_id', async () => {
      // Create a public agent (no org)
      const { data: publicAgent } = await serviceClient
        .from('fractal_agents')
        .insert({
          name: 'Public Agent',
          type: 'specialist',
          organization_id: null,
          description: 'Public agent'
        })
        .select()
        .single()

      // User A tries to read the public agent
      const { data: readAttempt } = await userAClient
        .from('fractal_agents')
        .select()
        .eq('id', publicAgent?.id)

      // Should be able to read public agents
      expect(readAttempt).toHaveLength(1)
    })
  })

  describe('Agent Collective Memory RLS', () => {
    it('should isolate memory by organization_id', async () => {
      // Create memory entries for both orgs
      const { data: memoryA } = await serviceClient
        .from('agent_collective_memory')
        .insert({
          task_type: 'analysis',
          input_context: 'Test context A',
          organization_id: TEST_USER_A.id,
          success: true
        })
        .select()
        .single()

      const { data: memoryB } = await serviceClient
        .from('agent_collective_memory')
        .insert({
          task_type: 'analysis',
          input_context: 'Test context B',
          organization_id: TEST_USER_B.id,
          success: true
        })
        .select()
        .single()

      // User A tries to read Memory B
      const { data: readAttempt } = await userAClient
        .from('agent_collective_memory')
        .select()
        .eq('id', memoryB?.id)

      // Should not be able to read other org's memory
      expect(readAttempt).toEqual([])
    })
  })

  describe('Audit Logs RLS', () => {
    it('should prevent non-admin users from reading audit logs', async () => {
      // Create an audit log entry
      const { data: auditLog } = await serviceClient
        .from('audit_logs')
        .insert({
          event_type: 'test_event',
          event_action: 'read',
          user_id: TEST_USER_A.id,
          organization_id: TEST_USER_A.id
        })
        .select()
        .single()

      // User A tries to read the audit log
      const { data: readAttempt, error } = await userAClient
        .from('audit_logs')
        .select()
        .eq('id', auditLog?.id)

      // Should not be able to read audit logs (admin only)
      expect(readAttempt).toEqual([])
    })
  })

  describe('Encrypted Secrets RLS', () => {
    it('should isolate secrets by organization_id', async () => {
      // Create secrets for both orgs
      const { data: secretA } = await serviceClient
        .from('encrypted_secrets')
        .insert({
          organization_id: TEST_USER_A.id,
          secret_key: 'test_api_key_a',
          secret_type: 'api_key',
          encrypted_value: Buffer.from('encrypted_value_a')
        })
        .select()
        .single()

      const { data: secretB } = await serviceClient
        .from('encrypted_secrets')
        .insert({
          organization_id: TEST_USER_B.id,
          secret_key: 'test_api_key_b',
          secret_type: 'api_key',
          encrypted_value: Buffer.from('encrypted_value_b')
        })
        .select()
        .single()

      // User A tries to read Secret B
      const { data: readAttempt } = await userAClient
        .from('encrypted_secrets')
        .select()
        .eq('id', secretB?.id)

      // Should not be able to read other org's secrets
      expect(readAttempt).toEqual([])
    })
  })
})
