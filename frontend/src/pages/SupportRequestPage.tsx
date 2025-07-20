import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Button } from '../components/ui/Button';
import { Customer } from '../models/Customer';
import { customerService } from '../services/ApiService';

interface SupportTicket {
  subject: string;
  category: string;
  priority: string;
  description: string;
  orderId?: string;
}

export const SupportRequestPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const orderIdFromUrl = searchParams.get('order');
  
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [ticket, setTicket] = useState<SupportTicket>({
    subject: '',
    category: 'general',
    priority: 'medium',
    description: '',
    orderId: orderIdFromUrl || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const categories = [
    { value: 'general', label: 'General Inquiry' },
    { value: 'order', label: 'Order Issue' },
    { value: 'shipping', label: 'Shipping Question' },
    { value: 'return', label: 'Return/Refund' },
    { value: 'product', label: 'Product Question' },
    { value: 'account', label: 'Account Issue' },
    { value: 'technical', label: 'Technical Support' },
    { value: 'billing', label: 'Billing Question' }
  ];

  const priorities = [
    { value: 'low', label: 'Low', description: 'General questions, not urgent' },
    { value: 'medium', label: 'Medium', description: 'Standard issues, response within 24 hours' },
    { value: 'high', label: 'High', description: 'Urgent issues, response within 4 hours' },
    { value: 'critical', label: 'Critical', description: 'Emergency issues, immediate response needed' }
  ];

  useEffect(() => {
    loadCustomerData();
  }, []);

  const loadCustomerData = async () => {
    try {
      setLoading(true);
      const customerData = await customerService.getCurrentCustomer();
      setCustomer(customerData);
    } catch (err) {
      console.error('Failed to load customer data:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!ticket.subject.trim()) newErrors.subject = 'Subject is required';
    if (!ticket.description.trim()) newErrors.description = 'Description is required';
    if (ticket.description.length < 10) newErrors.description = 'Description must be at least 10 characters';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);

      // In a real application, this would send to a support ticket API
      const supportTicket = {
        ...ticket,
        customer_id: customer?.id,
        customer_email: customer?.email,
        created_at: new Date().toISOString(),
        status: 'open'
      };

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      console.log('Support ticket submitted:', supportTicket);
      
      setSubmitted(true);
      setMessage({ 
        type: 'success', 
        text: 'Your support request has been submitted successfully. You will receive a response within 24 hours.' 
      });

      // Reset form
      setTicket({
        subject: '',
        category: 'general',
        priority: 'medium',
        description: '',
        orderId: ''
      });

    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: 'Failed to submit support request. Please try again.' 
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-4">Support Request Submitted!</h1>
              <p className="text-gray-600 mb-6">
                Thank you for contacting us. We've received your support request and will get back to you soon.
              </p>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-gray-600">What happens next?</p>
                <ul className="text-sm text-gray-700 mt-2 space-y-1">
                  <li>• You'll receive an email confirmation</li>
                  <li>• Our support team will review your request</li>
                  <li>• We'll respond based on your selected priority level</li>
                  <li>• You can track your ticket status via email</li>
                </ul>
              </div>
              <div className="space-y-3">
                <Link to="/orders">
                  <Button variant="secondary" className="w-full">
                    View My Orders
                  </Button>
                </Link>
                <Link to="/">
                  <Button className="w-full">
                    Back to Home
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Contact Support</h1>
          <p className="text-gray-600">
            Need help? Submit a support request and our team will get back to you.
          </p>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-100 text-green-800 border border-green-200' 
              : 'bg-red-100 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Customer Info Display */}
            {customer && (
              <div className="bg-gray-50 rounded p-4">
                <p className="text-sm text-gray-600">Submitting as:</p>
                <p className="font-medium">{customer.firstName} {customer.lastName}</p>
                <p className="text-sm text-gray-600">{customer.email}</p>
              </div>
            )}

            {/* Subject */}
            <div>
              <label className="block text-sm font-medium mb-2">Subject *</label>
              <input
                type="text"
                value={ticket.subject}
                onChange={(e) => setTicket({ ...ticket, subject: e.target.value })}
                className={`w-full border rounded px-3 py-2 ${errors.subject ? 'border-red-500' : ''}`}
                placeholder="Brief description of your issue"
              />
              {errors.subject && <p className="text-red-500 text-sm mt-1">{errors.subject}</p>}
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium mb-2">Category</label>
              <select
                value={ticket.category}
                onChange={(e) => setTicket({ ...ticket, category: e.target.value })}
                className="w-full border rounded px-3 py-2"
              >
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium mb-2">Priority</label>
              <div className="space-y-2">
                {priorities.map((priority) => (
                  <label key={priority.value} className="flex items-start space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="priority"
                      value={priority.value}
                      checked={ticket.priority === priority.value}
                      onChange={(e) => setTicket({ ...ticket, priority: e.target.value })}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium">{priority.label}</div>
                      <div className="text-sm text-gray-600">{priority.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Order ID */}
            <div>
              <label className="block text-sm font-medium mb-2">Order ID (Optional)</label>
              <input
                type="text"
                value={ticket.orderId}
                onChange={(e) => setTicket({ ...ticket, orderId: e.target.value })}
                className="w-full border rounded px-3 py-2"
                placeholder="Enter order ID if this relates to a specific order"
              />
              <p className="text-sm text-gray-600 mt-1">
                If your question is about a specific order, please include the order ID.
              </p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-2">Description *</label>
              <textarea
                value={ticket.description}
                onChange={(e) => setTicket({ ...ticket, description: e.target.value })}
                rows={6}
                className={`w-full border rounded px-3 py-2 ${errors.description ? 'border-red-500' : ''}`}
                placeholder="Please provide a detailed description of your issue or question. Include any relevant information that might help us assist you better."
              />
              {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
              <p className="text-sm text-gray-600 mt-1">
                Minimum 10 characters. Be as specific as possible to help us resolve your issue quickly.
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <Link to="/">
                <Button variant="secondary">
                  Cancel
                </Button>
              </Link>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Submit Request'}
              </Button>
            </div>
          </form>
        </div>

        {/* FAQ Section */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-4">Frequently Asked Questions</h3>
          <div className="space-y-3 text-sm">
            <div>
              <p className="font-medium text-blue-800">How long does it take to get a response?</p>
              <p className="text-blue-700">We typically respond within 24 hours for most inquiries, faster for urgent issues.</p>
            </div>
            <div>
              <p className="font-medium text-blue-800">Can I track my support ticket?</p>
              <p className="text-blue-700">Yes, you'll receive email updates about your ticket status and responses.</p>
            </div>
            <div>
              <p className="font-medium text-blue-800">What information should I include?</p>
              <p className="text-blue-700">Include order numbers, product details, error messages, and steps you've already tried.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};