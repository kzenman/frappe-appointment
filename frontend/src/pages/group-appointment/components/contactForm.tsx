/**
 * External dependencies
 */
import { ChangeEvent } from "react";

/**
 * Internal dependencies
 */
import { Input } from "@/components/input";
import Typography from "@/components/typography";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/select";

interface CompanyOption {
  value: string;
  label: string;
}

interface ContactFormProps {
  fullName: string;
  email: string;
  phone: string;
  onFullNameChange: (value: string) => void;
  onEmailChange: (value: string) => void;
  onPhoneChange: (value: string) => void;
  onEmailBlur: () => void;
  onPhoneBlur: () => void;
  companyOptions: CompanyOption[];
  selectedCompany: string;
  onCompanyChange: (value: string) => void;
  disabled?: boolean;
}

const ContactForm = ({
  fullName,
  email,
  phone,
  onFullNameChange,
  onEmailChange,
  onPhoneChange,
  onEmailBlur,
  onPhoneBlur,
  companyOptions,
  selectedCompany,
  onCompanyChange,
  disabled,
}: ContactFormProps) => {
  return (
    <div className="w-full flex flex-col gap-3 py-2">
      <Typography variant="h3" className="text-sm font-semibold">
        Your contact info
      </Typography>

      {companyOptions.length > 1 && (
        <Select
          value={selectedCompany}
          onValueChange={onCompanyChange}
          disabled={disabled}
        >
          <SelectTrigger className="active:ring-blue-400 focus:ring-blue-400">
            <SelectValue placeholder="Select a location" />
          </SelectTrigger>
          <SelectContent>
            {companyOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <Input
        disabled={disabled}
        placeholder="Full Name *"
        value={fullName}
        onChange={(e: ChangeEvent<HTMLInputElement>) =>
          onFullNameChange(e.target.value)
        }
        className="active:ring-blue-400 focus-visible:ring-blue-400"
      />
      <Input
        disabled={disabled}
        type="email"
        placeholder="Email *"
        value={email}
        onChange={(e: ChangeEvent<HTMLInputElement>) =>
          onEmailChange(e.target.value)
        }
        onBlur={onEmailBlur}
        className="active:ring-blue-400 focus-visible:ring-blue-400"
      />
      <Input
        disabled={disabled}
        type="tel"
        placeholder="Phone (optional)"
        value={phone}
        onChange={(e: ChangeEvent<HTMLInputElement>) =>
          onPhoneChange(e.target.value)
        }
        onBlur={onPhoneBlur}
        className="active:ring-blue-400 focus-visible:ring-blue-400"
      />
    </div>
  );
};

export default ContactForm;
