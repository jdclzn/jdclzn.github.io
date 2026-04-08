# frozen_string_literal: true

require "date"
require "psych"
require "jekyll-compose/file_mover"

module Jekyll
  module Compose
    class FileMover
      private

      def update_front_matter
        content = File.read(from)
        return unless content =~ Jekyll::Document::YAML_FRONT_MATTER_REGEXP

        content = $POSTMATCH
        match = Regexp.last_match[1] if Regexp.last_match
        data = movement.front_matter(load_front_matter(match))
        normalize_timestamps!(data)

        File.write(from, "#{Psych.dump(data)}---\n#{content}")
      rescue Psych::SyntaxError => e
        Jekyll.logger.warn e
      rescue StandardError => e
        Jekyll.logger.warn e
      end

      def load_front_matter(front_matter)
        Psych.safe_load(
          front_matter,
          permitted_classes: [Date, DateTime, Time]
        ) || {}
      end

      def normalize_timestamps!(data)
        %w[date last_modified_at].each do |key|
          data[key] = normalize_timestamp(data[key]) if data.key?(key)
        end
      end

      def normalize_timestamp(value)
        case value
        when Time, DateTime
          value.strftime("%Y-%m-%d %H:%M:%S %z")
        when Date
          value.strftime("%Y-%m-%d")
        else
          value
        end
      end
    end
  end
end
